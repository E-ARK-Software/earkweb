"""Solr client"""
import logging
import re
import tarfile
from urllib.parse import urlencode
from urllib.request import urlopen, Request

import pytz
from urllib.parse import quote
from eatb.file_format import FormatIdentification
from eatb.utils import randomutils
from eatb.utils.datetime import current_date
from eatb.utils.fileutils import list_files_in_dir
from datetime import datetime
from access.search.solrdocparams import SolrDocParams
from config.configuration import verify_certificate, representations_directory, metadata_directory, \
    metadata_fields_list, data_directory_pattern, node_namespace_id, repo_id, urn_file_pattern
from eatb.utils.fileutils import to_safe_filename
from taskbackend.taskutils import is_content_data_path, find_metadata_file 

logger = logging.getLogger(__name__)
import os
import json
import shutil
import urllib

import lxml.etree as etree
import unittest

import requests


def default_reporter(percent):
    print("\rProgress: {percent:3.0f}%".format(percent=percent))


class SolrClient(object):

    ffid = None

    def __init__(self, solr_server, collection):
        """
        Constructor to initialise solr client API URL

        @type       solr_server: SolrServer
        @param      solr_server: Solr server

        @type       collection: string
        @param      collection: Collection identifier, e.g. "samplecollection"
        """
        base_url = solr_server.get_base_url()
        if base_url[-1] != '/':
            base_url += '/'
        self.url = base_url + collection
        self.ffid = FormatIdentification()

    def select_params_suffix(self, params_suffix, rows=1000, start=0):
        """
        Search Solr, return URL and JSON response

        @type       params: string
        @param      params: Parameter suffix

        @rtype: string, int
        @return: Return url and return code
        """
        url = self.url + '/select?q=%s&rows=%d&start=%d&wt=json' % (urllib.quote(params_suffix), rows, start)
        conn = urlopen(url)
        return url, json.load(conn)

    def select(self, params):
        """
        Search Solr, return URL and JSON response

        @type       params: string
        @param      params: Query parameters

        @rtype: string, int
        @return: Return url and return code
        """
        params['wt'] = 'json'
        url = self.url + '/select?' + urllib.urlencode(params)
        conn = urlopen(url)
        return url, json.load(conn)

    def delete(self, query):
        """
        Delete query result documents

        @type       query: string
        @param      query: query

        @rtype: string, int
        @return: Return url and return code
        """
        params = {}
        url = self.url + '/update?' + urllib.urlencode(params)
        request = Request(url)
        request.add_header('Content-Type', 'text/xml; charset=utf-8')
        request.add_data('<delete><query>{0}</query></delete>'.format(query))
        response = urlopen(request).read()
        status = etree.XML(response).findtext('lst/int')
        return url, status

    def update(self, docs):
        """
        Post a list of documents

        @type       docs: list
        @param      docs: List of solr documents

        @rtype: string, int
        @return: Return url and return code
        """
        url = self.url + '/update?commit=true'
        add_xml = etree.Element('add')
        for doc in docs:
            xdoc = etree.SubElement(add_xml, 'doc')
            for key, value in doc.items():
                if value:
                    field = etree.Element('field', name=key)
                    field.text = str(value)
                    xdoc.append(field)
        request = Request(url)
        request.add_header('Content-Type', 'text/xml; charset=utf-8')
        request.data =etree.tostring(add_xml, pretty_print=True)
        response = urlopen(request).read()
        status = etree.XML(response).findtext('lst/int')
        return url, status

    def post_file_document(self, file_path, identifier, entry):
        """
        Iterate over tar file and post documents it contains to Solr API (extract)

        @type       file_path: string
        @param      file_path: Absolute path to file

        @type       identifier: string
        @param      identifier: Identifier of the tar package

        @type       entry: string
        @param      entry: entry name
        """
        puid = self.ffid.identify_file(file_path)
        content_type = self.ffid.get_mime_for_puid(puid)
        docs = []
        document = {"package": identifier, "path": entry, "content_type": content_type}
        docs.append(document)
        _, status = self.update(docs)
        return status

    

    def post_tar_file(self, tar_file_path, identifier, version, progress_reporter=default_reporter, task_log=None):
        """
        Iterate over tar file and post documents it contains to Solr API (extract)

        @type       tar_file_path: string
        @param      tar_file_path: Absolute path to tar file

        @type       identifier: string
        @param      identifier: Identifier of the tar package

        @rtype: list(dict(string, int))
        @return: Return list of urls and return codes
        """
        progress_reporter(0)
        tfile = tarfile.open(tar_file_path, 'r')
        extract_dir = '/tmp/temp-' + randomutils.randomword(10)
        results = []

        # Define regex pattern to match files under */representations/*/data/*
        data_directory_regex = re.compile(data_directory_pattern)
        #data_path_pattern = re.compile(r'.*/representations/.+/data/.*')

        task_log = task_log if task_log else logger
        
        # Check for metadata.json and load it if present
        metadata = {}
        try:
            tfile.extractall(extract_dir)
            metadata_file_path = find_metadata_file(extract_dir)
            if metadata_file_path and os.path.exists(metadata_file_path):
                with open(metadata_file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    task_log.info("Loaded metadata.json successfully.")
                    
                # Log each main level metadata key
                for key, value in metadata.items():
                    task_log.debug(f"Main metadata entry '{key}': {value}")
                    
            else:
                task_log.info("metadata.json not found in extracted files.")
        
        except json.JSONDecodeError as e:
            task_log.error(f"Failed to parse metadata.json: {e}")

        # Get number of files in tar
        numfiles = sum(1 for tarinfo in tfile if tarinfo.isreg())
        task_log.debug("Number of files in tarfile: %s " % numfiles)

        num = 0
        for t in tfile:
            afile = os.path.join(extract_dir, t.name)
            task_log.info(afile)
            if os.path.isfile(afile) and data_directory_regex.match(afile):
                params = SolrDocParams(afile).get_params()      
                params['literal.package'] = identifier
                params['literal.path'] = t.name
                params['literal.size'] = t.size
                params['literal.indexdate'] = current_date(time_zone_id='UTC')
                params['literal.archivedate'] = datetime.fromtimestamp(os.path.getctime(tar_file_path)).astimezone(pytz.UTC)
                params['literal.version'] = int(re.search(r'\d+', version).group(0))
                
                # 2. Add descriptions from file_metadata if they match the filename
                if 'representations' in metadata:
                    for rep_id, rep_data in metadata['representations'].items():
                        if 'file_metadata' in rep_data:
                            file_metadata = rep_data['file_metadata']
                            filename = os.path.basename(t.name)
                            if filename in file_metadata:
                                params['literal.filedescription'] = file_metadata[filename]
                                # Define the parameters you want to substitute
                                urn_params = {
                                    'node_namespace_id': node_namespace_id,
                                    'repo_id': repo_id,
                                    'encoded_package_id': quote(identifier, safe=''),
                                    'representation_id': rep_id,
                                    'encoded_file_path': quote(filename, safe='')
                                }
                                urn = urn_file_pattern.format(**urn_params)
                                params['literal.identifier'] = urn
                                params['literal.representation'] = repo_id
                                task_log.debug(f"Added description for '{filename}': {file_metadata[filename]}")

                # 3. Add main level metadata entries
                selected_main_keys = metadata_fields_list
                for main_key, main_value in metadata.items():
                    if main_key != "representations" and main_key in selected_main_keys:  # Skip representations as it's processed separately
                        params[f'literal.{main_key}'] = main_value
                        task_log.debug(f"Added main level metadata '{main_key}': {main_value}")

                files = {'file': ('userfile', open(afile, 'rb'))}
                post_url = '%s/update/extract?%s' % (self.url, urlencode(params))
                response = requests.post(post_url, files=files, verify=verify_certificate)
                result = {"url": post_url, "status": response.status_code}

                if response.status_code != 200:
                    status = self.post_file_document(afile, identifier, t.name)
                    if status == 200:
                        task_log.info("Posting file failed for URL '%s' with status code: %d. Posted plain document instead." % (post_url, response.status_code))
                    else:
                        task_log.info("Unable to create document for URL '%s'" % post_url)
                results.append(result)
                num += 1
                percent = num * 100 / numfiles
                progress_reporter(percent)

        self.commit()
        logger.info(f"Extract directory: {extract_dir}")
        #shutil.rmtree(extract_dir)
        progress_reporter(100)
        
    def index_directory(self, directory_path, identifier, version, progress_reporter=default_reporter, task_log=None):
        """
        Recursively iterate over files in a directory and post them to Solr.

        @type       directory_path: string
        @param      directory_path: Path to the directory containing content files

        @type       identifier: string
        @param      identifier: Identifier of the package

        @rtype: list(dict(string, int))
        @return: List of URLs and their corresponding return codes
        """
        progress_reporter(0)
        task_log = task_log if task_log else logger
        results = []

        # Load metadata.json if available
        metadata = {}
        metadata_file_path = find_metadata_file(directory_path)
        if metadata_file_path and os.path.exists(metadata_file_path):
            with open(metadata_file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                task_log.info("Loaded metadata.json successfully.")

        # Regex to match the valid file paths
        valid_path_regex = re.compile(data_directory_pattern)

        # Collect all files matching the pattern
        files_to_index = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory_path)
                if valid_path_regex.search(full_path):
                    files_to_index.append(full_path)

        numfiles = len(files_to_index)
        task_log.info(f"Found {numfiles} content files for indexing.")

        for num, file_path in enumerate(files_to_index, 1):
            params = SolrDocParams(file_path).get_params()
            params['literal.package'] = identifier
            params['literal.path'] = os.path.relpath(file_path, directory_path)
            params['literal.size'] = os.path.getsize(file_path)
            params['literal.indexdate'] = current_date(time_zone_id='UTC')
            params['literal.archivedate'] = datetime.fromtimestamp(os.path.getctime(file_path)).astimezone(pytz.UTC)
            params['literal.version'] = int(re.search(r'\d+', version).group(0))

            # Add descriptions and metadata
            filename = os.path.basename(file_path)
            if 'representations' in metadata and metadata['representations']:
                representation_items = metadata['representations'].items()
                print(representation_items)
                for rep_id, rep_data in representation_items:
                    if rep_data and 'file_metadata' in rep_data and rep_data['file_metadata'] and filename in rep_data['file_metadata']:
                        urn_params = {
                            'node_namespace_id': node_namespace_id,
                            'repo_id': repo_id,
                            'encoded_package_id': quote(identifier, safe=''),
                            'representation_id': rep_id,
                            'encoded_file_path': quote(filename, safe='')
                        }
                        urn = urn_file_pattern.format(**urn_params)
                        params['literal.identifier'] = urn
                        params['literal.representation'] = rep_data['distribution_label']
                        params['literal.rights'] = rep_data['access_rights']
                        params['literal.label'] = rep_data['file_metadata'][filename]
                        task_log.debug(f"Added description for '{filename}': {rep_data['file_metadata'][filename]}")

            # Add main level metadata entries
            selected_main_keys = metadata_fields_list
            for main_key, main_value in metadata.items():
                if main_key != "representations" and main_key in selected_main_keys:
                    params[f'literal.{main_key}'] = main_value
                    task_log.debug(f"Added main level metadata '{main_key}': {main_value}")

            # Post file to Solr
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': ('userfile', f)}
                    post_url = f"{self.url}/update/extract?{urlencode(params)}"
                    response = requests.post(post_url, files=files, verify=verify_certificate)
                    result = {"url": post_url, "status": response.status_code}
                    results.append(result)

                    if response.status_code != 200:
                        task_log.info(f"Failed to post '{file_path}' (status {response.status_code}).")
            except Exception as e:
                task_log.error(f"Error posting file '{file_path}': {str(e)}")

            percent = (num / numfiles) * 100
            progress_reporter(percent)

        self.commit()
        task_log.info(f"Finished indexing files in directory: {directory_path}")
        return results



    def commit(self):
        """
        Commit changes to Solr

        @rtype: string, int
        @return: Return url and return code
        """
        url = self.url + '/update?commit=true'
        response = urlopen(url)
        return url, response.code


class TestSolr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    # def test_solr_post_document(self):
    #     slr = SolrClient("http://localhost:8983/solr/", "samplecollection")
    #     docs = []
    #     document = {"id":"1234abcde",
    #             "cat":"journal",
    #             "name":"Experiments on the go",
    #             "genre_s":"science"}
    #     docs.append(document)
    #     slr.update(docs)
    #     slr.commit()

    # def test_extract(self):
    #     slr = SolrClient("http://localhost:8983/solr/", "samplecollection")
    #     tar_file_path = "/opt/python_wsgi_apps/earkweb/testresources/storage-test/bar.tar"
    #     identifier = "739f9c5f-c402-42af-a18b-3d0bdc4e8751"
    #     results = slr.post_tar_file(tar_file_path, identifier)
    #     print results

if __name__ == '__main__':
    unittest.main()
