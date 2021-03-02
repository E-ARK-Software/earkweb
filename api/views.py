from __future__ import unicode_literals

import json
import re
import tarfile
import traceback
from json import JSONDecodeError

import magic
from dateutil import parser
from datetime import date, timedelta, datetime
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, \
    HttpResponseForbidden, FileResponse, HttpResponseNotAllowed, Http404, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from eatb.packaging.tar_entry_reader import ChunkedTarEntryReader
from eatb.storage.checksum import ChecksumFile, ChecksumAlgorithm
from eatb.storage.directorypairtreestorage import DirectoryPairtreeStorage, make_storage_data_directory_path
from eatb.utils.datetime import date_format, DT_ISO_FORMAT
from eatb.utils.fileutils import fsize, get_mime_type, read_file_content, list_files_in_dir, get_directory_json, \
    to_safe_filename, from_safe_filename
from eatb.utils.randomutils import randomword
from pairtree import ObjectNotFoundException
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, renderer_classes
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework_api_key.permissions import HasAPIKey
from api import serializers
from api.serializers import InformationPackageSerializer, InternalIdentifierSerializer
from api.util import get_representation_ids_by_label, get_representation_ids, DirectoryInfo
from earkweb.models import InformationPackage, InternalIdentifier, Representation
from earkweb.models import RepoUser
import os
import logging
from taskbackend.taskexecution import execute_task
from taskbackend.ip_state import IpState
from taskbackend.tasks import checkout_working_copy_from_storage, aip_indexing, \
    delete_representation_data_from_workdir, \
    rename_representation_directory, sip_package
from config.configuration import config_path_work, config_path_storage, file_size_limit, \
    representations_directory, config_max_http_download, node_namespace_id, default_org
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import parsers
from rest_framework import renderers
from uuid import uuid4
from rest_framework import generics
from util.djangoutils import check_required_params, get_unused_identifier

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def create_package(request, procid):
    """
    post:
    Create package (database, task queue)

    To start the package creation for a given working directory

        curl -v -X POST -H "Authorization: Token 16f733abd45c589867af5f72f5e0593ff3723010"
        http://127.0.0.1:8000/earkweb/api/informationpackages/dfd7d463-6560-4e0d-b8ec-1815e88513f4/create-package
    """
    if request.method == "POST":
        try:
            ip = InformationPackage.objects.get(process_id=procid)
            user = User.objects.get(pk=request.user.pk)
            logger.info("Package creation task for process id: %s started by user %s" % (ip.process_id, user.username))
            task_input = {
                "process_id": ip.process_id, "package_name": ip.package_name, "org_nsid": node_namespace_id
            }
            try:
                # Execute task
                job = sip_package.delay(json.dumps(task_input))
                data = {"success": True, "id": job.id}
            except AttributeError:
                errdetail = """An error occurred, the task was not initiated."""
                data = {"success": False, "errmsg": "Error ", "errdetail": errdetail}
        except InformationPackage.DoesNotExist:
            return JsonResponse({
                "success": False, "errmsg": "Information package record not found",
                "errdetail": "No information package record with ID '%s'" % procid}, status=404)
        except Exception as err:
            tb = traceback.format_exc()
            logging.error(str(tb))
            data = {"success": False, "errmsg": str(err), "errdetail": str(tb)}
            return JsonResponse(data, status=500)
        return JsonResponse(data, status=201)
    else:
        error = {"message": "Request method not supported"}
        return JsonResponse(error, status=400)


@csrf_exempt
@api_view(['POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def start_ingest(request, procid):
    """
    post:
    Start ingest (database, task queue)

    To start the ingest for a given submission run

        <code>curl -v -X POST -H "Authorization: Token 16f733abd45c589867af5f72f5e0593ff3723010"
        http://127.0.0.1:8000/earkweb/api/informationpackages/dfd7d463-6560-4e0d-b8ec-1815e88513f4/startingest
    """
    if request.method == "POST":
        try:
            # selected_ip = request.POST['selected_ip']
            ip = InformationPackage.objects.get(process_id=procid)
            user = User.objects.get(pk=request.user.pk)
            logger.info("Task processing for process id: %s started by user %s" % (ip.process_id, user.username))
            identifier = ip.identifier if ip.identifier \
                else "urn:uuid:%s:%s" % (node_namespace_id, get_unused_identifier(user.pk, False))
            ip.identifier = identifier
            ip.save()
            task_input = {
                "process_id": ip.process_id, "package_name": ip.package_name, "org_nsid": node_namespace_id,
                "identifier": identifier, "md_format": "METS"
            }
            data = execute_task(task_input)
        except InformationPackage.DoesNotExist:
            return JsonResponse({
                "success": False, "errmsg": "Information package record not found",
                "errdetail": "No information package record with ID '%s'" % procid}, status=404)
        except Exception as err:
            tb = traceback.format_exc()
            logging.error(str(tb))
            data = {"success": False, "errmsg": str(err), "errdetail": str(tb)}
            return JsonResponse(data, status=500)
        return JsonResponse(data, status=201)
    else:
        error = {"message": "Request method not supported"}
        return JsonResponse(error, status=400)


@csrf_exempt
@api_view(['POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
@renderer_classes([JSONRenderer])
def checkout_working_copy(request, identifier):
    """
    post:
    Checkout a working copy (database, file system)

    A stored data set without a working copy cannot to be edited or changed directly. It is required to checkout a
    working copy first.

    To checkout the information package use the following command:

        curl -X POST http://localhost:8000/earkweb/api/informationpackages/urn:uuid:42658bbd-a76f-46f5-85da-f0ad2bed94dc/checkout-working-copy/
    """
    data = None
    if request.body and request.body != "":
        try:
            data = JSONParser().parse(request)
        except ParseError as e:
            return JsonResponse(e.get_full_details(), status=400)
    metadata_only = True if data and 'metadataonly' in data and data['metadataonly'] == "true" else False
    reset_aip = request.query_params and 'reset' in request.query_params and request.query_params['reset'] == "true"
    try:
        ip = InformationPackage.objects.get(identifier=identifier)
        try:
            u = User.objects.get(username=request.user)
            #if u != ip.user:
            #    return JsonResponse({"message": "Unauthorized. Operation is not permitted."}, status=403)
            if ip.process_id != "":
                return JsonResponse({"message": "A working copy already exists."}, status=400)
            dpts = DirectoryPairtreeStorage(config_path_storage)
            if not dpts.identifier_object_exists(identifier):
                return JsonResponse({"message": "Object does not exist in storage."}, status=404)
            process_id = str(uuid4())
            task_input = {
                "identifier": identifier, "process_id": process_id,
                "metadataonly": metadata_only, "reset": reset_aip
            }
            job = checkout_working_copy_from_storage.delay(task_input)
            ip.process_id = process_id
            ip.work_dir = os.path.join(config_path_work, process_id)
            ip.save()
            return JsonResponse(
                {"message": "Checkout request submitted successfully.", "job_id": job.id, "process_id": process_id},
                status=201
            )
        except User.DoesNotExist:
            return JsonResponse({"message": "Internal error: user does not exist"}, status=500)
    except InformationPackage.DoesNotExist:
        return JsonResponse({"message": "Object does not exist"}, status=404)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def do_informationpackage_representation(request, process_id, representation_id):
    """
    delete: delete a representation (database, task queue)

    delete a representation
    """
    try:
        ip = InformationPackage.objects.get(process_id=process_id)
        try:
            u = User.objects.get(username=request.user)
            #if u != ip.user:
            #    return JsonResponse({"message": "Unauthorized. Operation is not permitted."}, status=403)
            job = delete_representation_data_from_workdir.delay(
                ('{"process_id": "%s", "representation_id": "%s"}' % (process_id, representation_id))
            )
            return JsonResponse(
                {"message": "Representation deletion request submitted successfully.", "job_id": job.id},
                status=200
            )
        except User.DoesNotExist:
            return JsonResponse({"message": "Internal error: user does not exist"}, status=500)
    except InformationPackage.DoesNotExist:
        return JsonResponse({"message": "object does not exist"}, status=404)


@csrf_exempt
@api_view(['PATCH'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def rename_representation(request, process_id, representation):
    """
    post: rename representation (database, task queue)

    rename representation
    """
    try:
        ip = InformationPackage.objects.get(process_id=process_id)

        new_representation_dir = request.GET.get('new_representation_dir', None)
        if not new_representation_dir:
            return JsonResponse({"message": "New representation id parameter missing."}, status=400)
        try:
            u = User.objects.get(username=request.user)
            #if u != ip.user:
            #    return JsonResponse({"message": "Unauthorized. Operation is not permitted."}, status=403)

            job = rename_representation_directory.delay((
                '{"process_id": "%s", "current_representation_dir": "%s", "new_representation_dir": "%s"}'
                % (process_id, representation, new_representation_dir)
            ))
            return JsonResponse(
                {"message": "Rename representation request submitted successfully.", "job_id": job.id},
                status=200
            )
        except User.DoesNotExist:
            return JsonResponse({"message": "Internal error: user does not exist"}, status=500)
    except InformationPackage.DoesNotExist:
        return JsonResponse({"message": "object does not exist"}, status=404)


@csrf_exempt
@api_view(['POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def identifiers_by_extuid(request):
    """
    post: Get persistent identifier and process identifier for external unique identifier (database)

    Either a single value or comma separated list of external unique identifiers can by posted to this function
    which will return a list of triples each of which contains the external unique identifier, the persistent
    identifier, and the external unique identifier.

    To retrieve the id pairs for a single external unique identifier:

        curl -v -d 'https://github.com/agconti/kaggle-titanic'
        -X POST http://localhost:8000/earkweb/api/identifiers-by-extuid/

    To retrieve the id pairs for a list of external unique identifiers use a comma separated list:

        curl -v -d
        'https://github.com/agconti/kaggle-titanic,http://ec.europa.eu/eurostat/web/products-informationpackages/-/tps00189'
        -X POST http://localhost:8000/earkweb/api/identifiers-by-extuid/

    The result will be returned as a list of identifier groups ("ids"):

        <code><pre>{
          "ids": [{
            "external-id": "https://github.com/agconti/kaggle-titanic",
            "persistent-id": "urn:uuid:e369c4ddd9c7f220e13aa7bf4740313bfc879eac",
            "process-id": "7513d6b9-583e-4673-8aba-ae1698d3387c"
          }, {
            "external-id": "http://ec.europa.eu/eurostat/web/products-informationpackages/-/tps00189",
            "persistent-id": "urn:uuid:c0927d689d76722ba878a664aca47f490a700819",
            "process-id": "d510acc8-a22b-4a33-98cc-4af18264771b"
          }, {
            "external-id": "doi:xyz/ajs62",
            "persistent-id": "",
            "process-id": "e39cf59c-b819-4274-a1df-b2e86e688140"
          }]
        }</pre>

    <code>external-id</code> is an external identifier which was posted with the request, <code>persistent-id</code> is a
    unique persistent identifier of the item, and <code>process-id</code> is an existing process which exists for
    creating a new or modifying an existing package. If <code>persistent-id</code> is empty, it means that there is an
    open submission or change process for the corresponding dataset and that it is still not stored in the repository.
    If <code>process-id</code> is empty this means that the data set is stored in the repository and the process
    directory does not exist any more (it can be created again by checking out the data set, see API function
    <code>checkout-working-copy</code>).
    """
    if request.method == "POST":
        try:
            if not request.body:
                return JsonResponse("No input provided", status=400)
            extuidcsl = request.body.decode('utf-8')
            extuids = extuidcsl.split(",")
            ips = list(InformationPackage.objects.filter(extuid__in=extuids).values_list(
                "external_id", "process_id", "identifier", "deleted")
            )
            res = [{"external-id": ip[0], "process-id": ip[1], "persistent-id": ip[2], "deleted": ip[3]} for ip in ips]
            result = {"ids": res}
            return JsonResponse(result, status=200)
        except Exception as err:
            logger.error(err)
            return JsonResponse({"message": "object does not exist"}, status=404)
    else:
        error = {"message": "Request method not supported"}
        return JsonResponse(error, status=400)


@csrf_exempt
@api_view(['POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def index_informationpackage(request, identifier):
    """
    post:
    Index data set (file system, indexing service)

    Full-text index files contained in packages.

    Example

        http://127.0.0.1:8000/earkweb/api/index/ait:3a274aaf091368aea1df4fb2f03b13bf69c78e93
    """
    try:
        ip = InformationPackage.objects.get(identifier=identifier)
        try:
            u = User.objects.get(username=request.user)
            #if u != ip.user:
            #    return JsonResponse({"message": "Unauthorized. Operation is not permitted."}, status=403)
            dpts = DirectoryPairtreeStorage(config_path_storage)
            if not dpts.identifier_object_exists(identifier):
                return JsonResponse({"message": "Data asset does not exist in storage."}, status=404)
            job = aip_indexing.delay(('{"identifier": "%s"}' % identifier))
            return JsonResponse({"message": "Indexing request submitted successfully.", "job_id": job.id}, status=201)
        except User.DoesNotExist:
            return JsonResponse({"message": "Internal error: user does not exist"}, status=500)
    except InformationPackage.DoesNotExist:
        return JsonResponse({"message": "object does not exist"}, status=404)


@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def informationpackage_representations_info(request, process_id):
    """
    get: Get representation ids by label (database, file system)

    Requires the metadata file to look up labels and find the corresponding representation id.
    """
    working_directory = os.path.join(config_path_work, process_id)
    try:
        representation_ids = get_representation_ids(working_directory)
        representations_info = {}
        for representation_id in representation_ids:
            representation_data_path = os.path.join(working_directory, representations_directory, representation_id,
                                                    "data")
            representations_info[representation_id] = DirectoryInfo(representation_data_path).summary()
        return JsonResponse(representations_info, status=200)
    except Http404 as e:
        return HttpResponseNotFound(e.__str__())
    except ValueError as e:
        return HttpResponseServerError({"message": e.__str__()})


@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def informationpackage_representation_info_by_label(request, process_id, representation_label):
    """
    get: Get representation ids by label (database, file system)

    Requires the metadata file to look up labels and find the corresponding representation id.
    """
    working_directory = os.path.join(config_path_work, process_id)
    try:
        representation_ids = get_representation_ids_by_label(working_directory, representation_label)
        representations_info = {}
        for representation_id in representation_ids:
            representation_data_path = os.path.join(working_directory, representations_directory, representation_id,
                                                    "data")
            representations_info[representation_id] = DirectoryInfo(representation_data_path).summary()
        return JsonResponse(representations_info, status=200)
    except Http404 as e:
        return HttpResponseNotFound(e.__str__())
    except ValueError as e:
        return HttpResponseServerError({"message": e.__str__()})


@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def processing_file_resource(request, processing, resource_path):
    """
    get: Read processing log (database, file system)
    """
    username = request.user.username
    file_path = os.path.join(config_path_processing, username, processing, resource_path)
    return read_file(file_path)



@csrf_exempt
@api_view(['GET', 'DELETE'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def do_working_dir_file_resource(request, process_id, ip_sub_file_path):
    """
    get: Retrieve file resource (database, file system)

    Retrieve file resource from the working area's file system.
    For example, the following is a request to retrieve a metadata file named `metadata.json` from  the metadata folder
    in the working directory:

        http://localhost:8000/earkweb/api/informationpackages/cb755987-9e83-4e71-b000-dea9324e5dea/file-resource/metadata%2Fmetadata.json/

    delete: Remove file resource (database, working area)

    Retrieve file resource
    """
    if request.method == 'GET':
        file_path = os.path.join(config_path_work, process_id, ip_sub_file_path)
        return read_file(file_path)
    elif request.method == 'DELETE':
        try:
            ip = InformationPackage.objects.get(process_id=process_id)
            try:
                u = User.objects.get(username=request.user)
                #if u != ip.user:
                #    return JsonResponse({"message": "Unauthorized. Operation is not permitted."}, status=403)
            except User.DoesNotExist:
                return JsonResponse({"message": "Internal error: user does not exist"}, status=500)
            try:
                if ip_sub_file_path.startswith("/"):
                    msg = "File path should be relative to the working directory. Please omit leading slash."
                    return HttpResponseBadRequest({"message": msg})
                file = os.path.join(config_path_work, ip.process_id, ip_sub_file_path)
                if not os.path.exists(file):
                    return HttpResponseNotFound("File not found in working directory")
                os.remove(file)
                if not os.path.exists(file):
                    return JsonResponse({"message": "File successfully removed"}, status=200)
                else:
                    return HttpResponseForbidden({"message": "Unable to remove file"})
            except OSError:
                return HttpResponseForbidden()
        except InformationPackage.DoesNotExist:
            return HttpResponseNotFound("Information package object not found in database")
    else:
        raise ValueError("Method not supported")


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def do_storage_file_resource(_, identifier, ip_sub_file_path):
    """
    get: Retrieve file resource (file system)

    Retrieve file resource from the storage area's file system.
    For example, the following is a request to retrieve a packaged data set from the storage area:

        http://localhost:8000/earkweb/api/informationpackages/urn%3Auuid%3A42658bbd-a76f-46f5-85da-f0ad2bed94dc/file-resource/urn%2Buuid%2B42658bbd-a76f-46f5-85da-f0ad2bed94dc.tar/

    Note that in the filename the colon of the identifier is mapped to '+' so that the identifier:

        urn:uuid:42658bbd-a76f-46f5-85da-f0ad2bed94dc

    results in the following filename:

        urn+uuid+42658bbd-a76f-46f5-85da-f0ad2bed94dc.tar

    which in URL encoded form is:

        urn%2Buuid%2B42658bbd-a76f-46f5-85da-f0ad2bed94dc.tar

    """
    dpts = DirectoryPairtreeStorage(config_path_storage)
    package_id = from_safe_filename(identifier)
    version = dpts.curr_version(package_id)
    access_path = os.path.join(make_storage_data_directory_path(package_id, config_path_storage), version)
    file_path = os.path.join(access_path, to_safe_filename(identifier), ip_sub_file_path)
    return read_file(file_path)


def read_file(file_path):
    if not os.path.exists(file_path):
        return HttpResponseNotFound("File not found %s" % file_path)
    elif not os.path.isfile(file_path):
        return HttpResponseBadRequest("Not a file")
    else:
        file_size = fsize(file_path)
        mime = get_mime_type(file_path)
        if file_size > config_max_http_download:
            return HttpResponseForbidden(
                "Size of requested file exceeds limit (file size %d > %d)" % (file_size, config_max_http_download))
        if file_path.lower().endswith(('.tar', '.tar.gz', 'zip')):
            stream = open(file_path, 'rb')
            response = FileResponse(stream, content_type=mime)
            response['Content-Disposition'] = "attachment; filename=%s" % os.path.basename(file_path)
            return response
        if file_size <= file_size_limit:
            file_content = read_file_content(file_path)
            if mime == "text/plain":
                mime = "text/plain;charset=utf-8"
            return HttpResponse(file_content, content_type=mime)
        else:
            return HttpResponseForbidden("Size of requested file exceeds limit (file size %d > %d)" %
                                         (file_size, file_size_limit))


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def package_entry_from_backend(_, identifier, entry):
    """
    get: Read package entry

    To read the CSV file 'weather.csv' (mime type: application/csv) from the data set named 'default' stored as part
    of the data set with identifier 'ait:faae219bffa999295175ff98e089fa0b07d9647d' use the following parameters:

    entry: data/weather.csv, identifier: ait:faae219bffa999295175ff98e089fa0b07d9647d, mime: application/csv,
    representation: default
    """
    try:
        dpts = DirectoryPairtreeStorage(config_path_storage)
        object_path = dpts.get_object_path(from_safe_filename(identifier))
        archive_file_path = os.path.join(object_path, "%s.tar" % identifier)
        t = tarfile.open(archive_file_path, 'r')
        tar_entry = os.path.join(identifier, entry)

        info = t.getmember(tar_entry)

        f = t.extractfile(info)
        start_bytes = f.read(256)

        inst = ChunkedTarEntryReader(t)
        magic_mime_detect = magic.Magic(mime=True)
        mime = magic_mime_detect.from_buffer(start_bytes)

        return HttpResponse(inst.chunks(tar_entry), content_type=mime)
    except ObjectNotFoundException:
        return JsonResponse(
            {"message": "The archival package does not exist: %s" % identifier}, status=404
        )
    except (KeyError):
        return JsonResponse(
            {"message": "Entry %s does not exist in archival package '%s'" % (entry, identifier)}, status=404
        )


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def get_ip_representations_info(_, identifier):
    """
    get:
        Get data set structure
    """
    try:
        dpts = DirectoryPairtreeStorage(config_path_storage)
        object_path = dpts.get_object_path(identifier)
        package_path = os.path.join(object_path, representations_directory)
        tar_files = list_files_in_dir(package_path)
        structure = {}
        for tar_file in tar_files:
            distribution_tar_path = os.path.join(package_path, tar_file)
            t = tarfile.open(distribution_tar_path, 'r')
            structure[tar_file] = t.getnames()
        return JsonResponse(structure, status=200)
    except ObjectNotFoundException:
        return JsonResponse({"message": "Information package does not exist in storage"}, status=404)


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def do_working_dir_dir_json(request, process_id):
    """
    get: List directory content as JSON (working area)

    List directory content as JSON
    """
    return directory_json(request, "work", process_id)


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def do_storage_dir_json(request, identifier):
    """
    get: List directory content as JSON (storage)

    List directory content as JSON
    """
    return directory_json(request, "storage", identifier)


def directory_json(request, area, item):
    """
    get:
    List directory content as JSON

    For example, to list the directory content of data set 'ait:faae219bffa999295175ff98e089fa0b07d9647d'
    (storage area), use the data set ID as 'item' value, for example:

        item: urn:uuid:faae219bffa999295175ff98e089fa0b07d9647d, area: storage

    For a listing of a submission or working copy (work area), use the process ID as 'item' value, for example:

        item: da992e2e-1eb0-4839-8cdd-688559cbbc39, area: work

    or run the following command:

        curl -X GET 'http://127.0.0.1:8000/earkweb/api/da992e2e-1eb0-4839-8cdd-688559cbbc39/dir-json'

    """
    version = 0  # N/A
    if area not in ["work", "storage", "processing"]:
        return JsonResponse({"message": "Area not defined."}, status=404)
    if area == "work":
        access_path = config_path_work
    elif area == "storage":
        dpts = DirectoryPairtreeStorage(config_path_storage)
        version = dpts.curr_version(item)
        access_path = os.path.join(make_storage_data_directory_path(item, config_path_storage), version)
    else:
        access_path = os.path.join(config_path_processing, request.user.username)
    if area in ["work", "storage"]:
        try:
            ip = InformationPackage.objects.get(process_id=item) if area == "work" else \
                InformationPackage.objects.get(identifier=item, version=version)
            try:
                u = User.objects.get(username=request.user)
                # if u != ip.user:
                #     return JsonResponse({"message": "Unauthorized. Access to this directory is not permitted."}, status=403)
            except User.DoesNotExist:
                return JsonResponse({"message": "Internal error: user does not exist"}, status=500)
        except InformationPackage.DoesNotExist:
            return JsonResponse({"message": "process does not exist"}, status=404)
        item_path = to_safe_filename(item)
    else:
        item_path = item
    if not os.path.exists(os.path.join(access_path, item_path)):
        return JsonResponse({
            "message": "Access path does not exist: %s" %
                       os.path.join(access_path, to_safe_filename(item))
        }, status=404)
    return JsonResponse(get_directory_json(access_path, item_path), status=200)


@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def submissions_list(request):
    """
    get:
    List all open submissions

    post:
    Initiate a new submission

    To initiate a new submission, at least the package_name must be provided in the json body:
    {"package_name": "mypackage_name"}).
    """

    if request.method == 'GET':
        snippets = InformationPackage.objects.all()
        serializer = InformationPackageSerializer(snippets, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        try:
            data = JSONParser().parse(request)
        except ParseError as e:
            return JsonResponse(e.get_full_details(), status=400)
        try:
            check_required_params(data, ["package_name"])
        except RuntimeError as e:
            error = {"message": "%s" % str(e)}
            return JsonResponse(error, status=400)
        process_id = str(uuid4())
        path = os.path.join(config_path_work, process_id)
        ips = InformationPackage.objects.filter(package_name=process_id)
        if ips.count() > 0:
            error = {"message": "Duplicate entry. A submission process with the given UUID already exists "}
            return JsonResponse(error, status=400)
        ips = InformationPackage.objects.filter(package_name=data['package_name'])
        if ips.count() > 0:
            error = {"message": "Duplicate entry. A submission process with the given name already exists"}
            return JsonResponse(error, status=400)
        package_name_pattern = r'^[a-z]{1,1}[a-z0-9]{2,40}$'
        if not re.search(package_name_pattern, data['package_name']):
            error = {"message": "The package_name must have at least 3 alphanumeric characters. "
                                "It must start with a character and can have a maximum length of 40 characters)"}
            return JsonResponse(error, status=400)

        extuid = data['extuid'] if 'extuid' in data else ''

        working_directory = os.path.join(config_path_work, process_id)
        if not os.path.exists(working_directory):
            os.makedirs(working_directory, exist_ok=True)

        state_data = json.dumps(
            {"version": 0, "last_change": date_format(datetime.datetime.utcnow(), fmt=DT_ISO_FORMAT)}
        )
        with open(os.path.join(working_directory, "state.json"), 'w') as status_file:
            status_file.write(state_data)

        serializer = InformationPackageSerializer(data=data)
        if serializer.is_valid():
            ip = InformationPackage.objects.create(process_id=process_id, identifier='',
                                                   package_name=data['package_name'],
                                                   work_dir=path, user=request.user, version=0, external_id=extuid)
            ip.save()
            return JsonResponse({
                "message": "Informationspaket-Paket erfolgreich erstellt.", "process_id": process_id
            }, status=201)
        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def submission_detail(request, procid):
    """
    get:
    Get details of a submission

    put:
    Update submission details.

    Parameters are defined in the request body in json format.
    In order to update dates (creation date, last change date), the date must be submitted in UTC.


            {
                "last_change": date_format(datetime.datetime.utcnow()),
                "created": date_format(datetime.datetime.utcnow()),
            }


    delete:
    Delete submission details
    """
    try:
        info_obj = InformationPackage.objects.get(process_id=procid)
    except InformationPackage.DoesNotExist:
        return HttpResponse(status=404)
    if request.method == 'GET':
        serializer = InformationPackageSerializer(info_obj)
        return JsonResponse(serializer.data)
    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = InformationPackageSerializer(info_obj, data=data)
        if serializer.is_valid():
            serializer.save()
            ip = InformationPackage.objects.get(process_id=info_obj.process_id)
            if "last_change" in data:
                ip.created = parser.parse(data["last_change"])
                logger.info("Updating last_change: %s (UTC)" % ip.last_change)
            if "created" in data:
                ip.created = parser.parse(data["created"])
                logger.info("Updating created: %s (UTC)" % ip.created)
            ip.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    elif request.method == 'DELETE':
        info_obj.deleted = True
        info_obj.save()
        return HttpResponse(status=204)


@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def int_id_list(request):
    """
    post: Create a new identifier (database)

    Example command:

        curl -X POST "http://localhost:8000/earkweb/api/identifiers/"

    Example response:

        {
          "message": "New identifier created successfully"
        }

    ait:9795d7581f3cf1d6aad815ca8e35fb1673d99a11

    get: Get an unused identifier (database)

    Example response:


    {
      "org_nsid": "repo",
      "identifier": "9795d7581f3cf1d6aad815ca8e35fb1673d99a11",
      "created": "2017-07-14T15:00:45.823277Z"
    }


    The indentifier string is composed by concatenating "org_nsid" and "identifier" separated by a colon sign, i.e.
    according to the example response the identifier would be

    ait:9795d7581f3cf1d6aad815ca8e35fb1673d99a11


    """
    if request.method == 'GET':
        snippet = InternalIdentifier.objects.filter(used=False)[:1]
        if len(snippet) == 0:
            return JsonResponse({"error": "No unused identifier available"}, status=404)
        snippet[0].used = True
        snippet[0].save()
        serializer = InternalIdentifierSerializer(snippet[0], many=False)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        try:
            if request.body:
                data = JSONParser().parse(request)
            else:
                data = {}
        except ParseError as e:
            return JsonResponse(e.get_full_details(), status=400)
        else:
            # identifier
            if 'identifier' not in data:
                data['identifier'] = randomword(40)
            identifier_pattern = r'^[a-z0-9-]{40,40}$'
            if not re.search(identifier_pattern, data['identifier']):
                error = {"message": "Identifier must be an alphanumeric string exactly 40 characters long"}
                return JsonResponse(error, status=400)
            data['org_nsid'] = None
            try:
                user = RepoUser.objects.get(pk=request.user.pk)
                data['org_nsid'] = user.org_nsid
            except RepoUser.DoesNotExist:
                pass
            if not data['org_nsid']:
                data['org_nsid'] = default_org
            if not data['org_nsid']:
                error = {"message": "The user's organization namespace identifier ('org_nsid') must be defined. "}
                return JsonResponse(error, status=500)
            org_nsid_pattern = r'^[a-z]{1,1}[a-z0-9]{2,20}$'
            if not re.search(org_nsid_pattern, data['org_nsid']):
                error = {"message": "The user's organization namespace identifier ('org_nsid') must have at least 3 "
                                    "alphanumeric characters. "
                                    "It must start with a character and can have a maximum length of 20 characters)"}
                return JsonResponse(error, status=500)
            ids = InternalIdentifier.objects.filter(org_nsid=data['org_nsid'], identifier=data['identifier'])
            if ids.count() > 0:
                error = {"message": "Duplicate entry. The identifier already exists for the organization's namespace. "}
                return JsonResponse(error, status=400)
            serializer = InternalIdentifierSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"message": "New identifier created successfully"}, status=201)
            return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def get_ip_states(request):
    """
    get:
        Status of all submissions (working area)

        Example

            http://localhost:8000/earkweb/api/informationpackages/status/
    """
    results = {}
    if request.method == 'GET':
        try:
            enddate = date.today()
            startdate = enddate - timedelta(days=7)
            ips = InformationPackage.objects.filter(created__range=[startdate, enddate])
            logger.debug(ips.query)
            for ip in ips:
                result = {}
                working_dir = os.path.join(config_path_work, ip.process_id)
                if os.path.exists(working_dir):
                    ip_state_file_path = os.path.join(working_dir, "state.json")
                    if os.path.exists(ip_state_file_path):
                        try:
                            info_file_content = read_file_content(ip_state_file_path)
                            result = json.loads(info_file_content)
                        except JSONDecodeError as err:
                            result = {"error": {
                                "title": "Error parsing state file",
                                "detail": "%s (line: %d, colum: %d)" % (err.msg, err.lineno, err.colno)}
                            }
                    else:
                        result = {"warning": {
                            "title": "State file not vailable",
                            "detail": "State file not found at: %s" % ip_state_file_path}
                        }
                results[ip.process_id] = result
            return JsonResponse(results, status=200)
        except Exception as err:
            logger.debug("Error", err)
            error = {"message": "An error occurred"}
            return JsonResponse(error, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def get_ip_state(request, process_id):
    """
    get:
        Status of selected submission (database, working area)

        Example

            http://localhost:8000/earkweb/api/informationpackages/08c261ce-2aec-412c-b245-7a64be495b03/status/
    """
    if request.method == 'GET':
        try:
            ip = InformationPackage.objects.get(process_id=process_id)
            result = {}
            working_dir = os.path.join(config_path_work, ip.process_id)
            if os.path.exists(working_dir):
                ip_state_file_path = os.path.join(working_dir, "state.json")
                if os.path.exists(ip_state_file_path):
                    try:
                        info_file_content = read_file_content(ip_state_file_path)
                        result = json.loads(info_file_content)
                    except JSONDecodeError as err:
                        result = {"error": {
                            "title": "Error parsing state file",
                            "detail": "%s (line: %d, colum: %d)" % (err.msg, err.lineno, err.colno)}
                        }
                else:
                    result = {"warning": {
                        "title": "State file not vailable",
                        "detail": "State file not found at: %s" % ip_state_file_path}
                    }
            return JsonResponse(result, status=200)
        except InformationPackage.DoesNotExist:
            error = {"message": "An error occurred"}
            return JsonResponse(error, status=500)


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def representations_list(request):
    """
    get: List representations of authenticated user (database)

    List representations of authenticated user
    """
    reps_qs = Representation.objects.select_related('ip').filter(ip__user=request.user.pk).order_by('-created')
    representations = {
        representations_directory: [
            {
                "unitIdentifier": r.identifier,
                "unitLabel": r.label,
                "unitName": r.ip.package_name,
                "ipIdentifier": r.ip.identifier
            }
            for r in reps_qs
        ]
    }
    return JsonResponse(representations, status=200)


class UploadFile(APIView):
    """
    post: Upload file to a submission or working copy (database, working area)

    The variable ${process_id} is the identifier of the process.

    The variable ${datatype} is one of "metadata", "data", or "documentation".

        curl -v -X POST -F "file=@${LOCAL_FILE_PATH}"
        http://127.0.0.1:8000/earkweb/api/informationpackages/${process_id}/${datatype}/upload/

    For example, to upload a metadatafile, and with `DATA_TYPE="metadata"`,
    `PROCESS_ID="08c261ce-2aec-412c-b245-7a64be495b03"`,
    and local file path `LOCAL_FILE_PATH="/home/user/dcat.xml`, the upload command would be as follows:

        curl -v -X POST -F "file=@/home/user/dcat.xml"
        http://127.0.0.1:8000/earkweb/api/informationpackages/08c261ce-2aec-412c-b245-7a64be495b03/metadata/upload/

    If a data set exists, the metadata file is also added to the last version of it.

    A data file can be added to a representation which is identified by the variable ${representation}.

    For example, add a data file to an information package, the file can be uploaded using the following curl command:

        curl -v -X POST -F "file=@${LOCAL_FILE_PATH}"
        http://127.0.0.1:8000/earkweb/api/informationpackages/${process_id}/${representation}/${datatype}/upload
        curl -v -H 'Authorization: Token 325dfabc9839904a117d446440232abaf344f9a0' -X POST -F "file=@/home/schlarbs/test.txt" http://localhost:8000/earkweb/api/informationpackages/73483984-debd-4d04-a14c-5acb11167719/36045801-af2f-4bc2-9df5-f3eeb9755904/data/upload/
    """
    throttle_classes = ()

    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    parser_classes = (parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = serializers.UploadedFileSerializer

    def post(self, request, process_id, datatype, representation=None):

        logger.info(self.get_view_name())

        if datatype not in ["metadata", "data", "documentation"]:
            error = {"message": "Data type not supported (must be 'metadata', 'data', or 'documentation'). "}
            return JsonResponse(error, status=400)

        # get information package object
        try:
            ip = InformationPackage.objects.get(process_id=process_id)
        except InformationPackage.DoesNotExist:
            return JsonResponse({"message": "The information package does not exist: %s" % process_id}, status=400)

        target_directory = None

        if datatype == "data" and not representation:
            representation = str(uuid4())
            reprec = Representation.objects.create(ip=ip, identifier=representation)
            reprec.save()

        if representation:
            representation_dir = os.path.join(config_path_work, process_id, representations_directory, representation)
            if not os.path.exists(representation_dir):
                os.makedirs(representation_dir, exist_ok=True)
                folders = ["metadata", "data", "documentation"]
                for folder in folders:
                    os.mkdir(os.path.join(representation_dir, folder))
            target_directory = os.path.join(config_path_work, process_id, representations_directory,
                                            representation, datatype)
        else:
            main_metadata_dir = os.path.join(config_path_work, process_id, "metadata/descriptive")

            if not os.path.exists(main_metadata_dir):
                os.makedirs(main_metadata_dir, exist_ok=True)
            target_directory = main_metadata_dir

        for key, value in request.FILES.items():

            uploaded_file = request.FILES.get(key, None)
            if not uploaded_file:
                error = {"message": "No upload file was specified."}
                return JsonResponse(error, status=status.HTTP_400_BAD_REQUEST)

            def handle_uploaded_file(f):
                with open(os.path.join(target_directory, str(uploaded_file)), 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)

            handle_uploaded_file(uploaded_file)

            # calculate sha
            sha256 = ChecksumFile(os.path.join(target_directory, str(uploaded_file))).get(ChecksumAlgorithm.SHA256)

            # Add metadata content to database record
            if datatype == "metadata" and str(uploaded_file).endswith("json"):
                try:
                    metadata_file_content = read_file_content(os.path.join(target_directory, str(uploaded_file)))
                    parsed_md = json.loads(metadata_file_content)
                    ip.basic_metadata = metadata_file_content
                    if "representations" in parsed_md:
                        for r, v in parsed_md["representations"].items():
                            try:
                                reprec = Representation.objects.get(ip=ip, identifier=r)
                            except Representation.DoesNotExist:
                                reprec = Representation.objects.create(ip=ip, identifier=r)
                            if "distribution_label" in v:
                                reprec.label = v["distribution_label"]
                            if "distribution_description" in v:
                                reprec.description = v["distribution_description"]
                            if "access_rights" in v:
                                reprec.accessRights = v["access_rights"]
                            reprec.license = 'undefined'
                            reprec.save()
                except JSONDecodeError:
                    return JsonResponse({"message": "error decoding JSON metadata file"},
                                        status=status.HTTP_400_BAD_REQUEST)

        # updating last change date
        ip = InformationPackage.objects.get(process_id=process_id)

        # using local time (converted to UTC in DB)
        ip.last_change = datetime.now()
        ip.save()
        logger.info("Last_change date updated: %s" % ip.last_change)
        response_data = {"message": "File upload successful", "sha256": sha256, 'processId': process_id}
        if representation:
            response_data["representationId"] = representation
        return JsonResponse(response_data, status=201)


class InformationPackages(generics.ListCreateAPIView):
    """
    get: List information packages (database)

    Get a list of information packages.

    post: Create an information package record (database)

    The submission process is initialized using the following command:

        curl -X POST -d 'package_name=${PACKAGE_NAME}' http://127.0.0.1:8000/earkweb/api/informationpackages/

    For example, with `PACKAGE_NAME='mypackage'`, the `curl` command would be:

        curl -X POST -d 'package_name=mypackage' 'http://127.0.0.1:8000/earkweb/api/informationpackages/'

    Example message in case of success (returns process ID):

        {"message": "Submission process initiated successfully.", "process_id": "08c261ce-2aec-412c-b245-7a64be495b03"}
    """
    serializer_class = InformationPackageSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        if self.request.user.id:
            #return InformationPackage.objects.filter(user=self.request.user.id)
            return InformationPackage.objects.filter()
        else:
            return InformationPackage.objects.all()


class InfPackDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    get: Get selected information package (database)

    Get selected information package (database)

    patch: Update information package record (database)

    Update information package record (replace record)

    put: Update information package record (database)

    Update information package record (update properties)

    delete: Delete registered information package (database)

    Delete registered information package
    """
    lookup_field = 'process_id'
    queryset = InformationPackage.objects.all()
    serializer_class = InformationPackageSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication,)
    permission_classes = [HasAPIKey | IsAuthenticated]


@csrf_exempt
@api_view(['GET'])
@authentication_classes((TokenAuthentication, BasicAuthentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def processing_dir_json(request, processing):
    """
    get: List directory content as JSON (working area)

    List directory content as JSON
    """
    return directory_json(request, "processing", processing)
