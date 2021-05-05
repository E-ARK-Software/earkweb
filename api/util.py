import json
import os
from json import JSONDecodeError

import magic
import requests
from PyPDF2 import PdfFileReader
from django.http import Http404

from config.configuration import django_backend_service_api_url, verify_certificate
from eatb.utils.fileutils import read_file_content, find_files
from util.djangoutils import get_user_api_token


def get_representation_ids(working_directory):
    if not os.path.exists(working_directory):
        raise Http404("Working directory not found")
    metadata_file_path = os.path.join(working_directory, "metadata/metadata.json")
    if not os.path.exists(metadata_file_path):
        raise Http404("Basic metadata not found")
    try:
        md_content = read_file_content(metadata_file_path)
        md = json.loads(md_content)
        if "representations" not in md:
            raise ValueError("Insufficient metadata")
        representation_ids = [k for k, v in md["representations"].items()]
        return representation_ids
    except JSONDecodeError:
        raise ValueError('Error parsing metadata')


def get_representation_ids_by_label(working_directory, representation_label):
    if not os.path.exists(working_directory):
        raise Http404("Working directory not found")
    metadata_file_path = os.path.join(working_directory, "metadata/metadata.json")
    if not os.path.exists(metadata_file_path):
        raise Http404("Basic metadata not found")
    try:
        md_content = read_file_content(metadata_file_path)
        md = json.loads(md_content)
        if "representations" not in md:
            raise ValueError("Insufficient metadata")
        representation_ids = [k for k, v in md["representations"].items() if
                              "distribution_label" in v and v["distribution_label"] == representation_label]
        return representation_ids
    except JSONDecodeError:
        raise ValueError('Error parsing metadata')


class DirectoryInfo(object):

    def __init__(self, root_directory):
        self.root_directory = root_directory

    def summary(self):

        report = {"mime_types": {}, "total_num_files": 0}
        contained_files = find_files(self.root_directory, "*")

        for contained_file in contained_files:
            report["total_num_files"] = report["total_num_files"] + 1
            mime_type = magic.Magic(mime=True).from_file(contained_file)
            if mime_type not in report["mime_types"]:
                report["mime_types"][mime_type] = 1
            else:
                report["mime_types"][mime_type] = report["mime_types"][mime_type] + 1
            if mime_type == "application/pdf":
                pdf = PdfFileReader(open(contained_file, 'rb'))
                num_pdf_pages = pdf.getNumPages()
                report["num_pdf_pages"] = report["num_pdf_pages"] + num_pdf_pages

        return report

    @staticmethod
    def summary_to_hr(summary):
        report_hr = {}
        for k, v in summary.items():
            key = k.replace("num", "number of").replace("_", " ")
            key = key[0].upper() + key[1:]
            report_hr[key] = v
        return report_hr


def data_sources_info_from_processing_input(request, processing_input):
    data_sources_info = []
    for data_source in processing_input.data_sources.all():
        data_source_info = {'identifier': data_source.ip.process_id, 'process_id': data_source.ip.process_id}
        query_url = "%s/datasets/%s/representations/info/" % (
            django_backend_service_api_url, data_source.ip.process_id)
        user_api_token = get_user_api_token(request.user)
        response = requests.get(query_url, headers={'Authorization': 'Token %s' % user_api_token},
                                verify=verify_certificate)
        if response.status_code == 200:
            try:
                data_source_info['info'] = json.loads(response.text)
                data_sources_info.append(data_source_info)
            except JSONDecodeError as err:
                raise ValueError('Error parsing response for source data request for process: %s, error: %s' %
                                          (data_source.source, err.__str__()))
        else:
            raise ValueError('Error retrieving source data for process id: %s' % data_source.source)
        return data_sources_info


class DirectoryInfo(object):

    def __init__(self, root_directory):
        self.root_directory = root_directory

    def summary(self):

        report = {"mime_types": {}, "total_num_files": 0}
        contained_files = find_files(self.root_directory, "*")

        for contained_file in contained_files:
            report["total_num_files"] = report["total_num_files"] + 1
            mime_type = magic.Magic(mime=True).from_file(contained_file)
            if mime_type not in report["mime_types"]:
                report["mime_types"][mime_type] = 1
            else:
                report["mime_types"][mime_type] = report["mime_types"][mime_type] + 1

        return report

    @staticmethod
    def summary_to_hr(summary):
        report_hr = {}
        for k, v in summary.items():
            key = k.replace("num", "number of").replace("_", " ")
            key = key[0].upper() + key[1:]
            report_hr[key] = v
        return report_hr
