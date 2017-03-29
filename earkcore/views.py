import logging
import urllib
import urllib2
from django.core.exceptions import ObjectDoesNotExist
import requests
from earkcore.search.solrclient import SolrClient
from earkcore.search.solrserver import SolrServer

from earkcore.utils.xmlutils import get_xml_schemalocations
from earkcore.xml.xmlschemanotfound import XMLSchemaNotFound

logger = logging.getLogger(__name__)
import os

from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from config.configuration import config_path_work
from config.configuration import config_path_storage
from config.configuration import config_path_reception

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseBadRequest

from earkcore.models import InformationPackage
from earkcore.storage.pairtreestorage import PairtreeStorage
from earkcore.utils.fileutils import read_file_content
from earkcore.filesystem.fsinfo import fsize, get_mime_type
from config.configuration import config_max_filesize_viewer
import base64
from django.template import RequestContext, loader
import json
from earkcore.filesystem.fsinfo import path_to_dict
from django.http import JsonResponse
from earkcore.utils import randomutils
from earkcore.process.cli.CliCommand import CliCommand
from subprocess import check_output

from earkcore.xml.xmlvalidation import XmlValidation
from workers.tasks import reception_dir_status, ip_save_metadata_file, set_process_state, index_aip_storage, repo_working_dir_exists, index_local_storage_ip_func, add_premis_event_ip_func
from workers.tasks import run_package_ingest

import traceback
#from xml.xmlvalidation import XmlValidation
#import lxml
from celery.result import AsyncResult
#from earkcore.models import DIP
#from earkcore.utils.randomutils import getUniqueID
#from workflow.models import WorkflowModules
#from workers.tasks import AIPtoDIPReset
#from django.core.urlresolvers import reverse

import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig
from django.shortcuts import render_to_response
import pprint
from config.configuration import storage_solr_server_ip
from config.configuration import storage_solr_core
from config.configuration import storage_solr_port
from collections import Counter
from workers.tasks import hdfs_batch_upload

import logging
logger = logging.getLogger(__name__)

class InformationPackageDetailView(DetailView):
    model = InformationPackage
    template_name = 'earkcore/ip_detail.html'


@login_required
def ipview(request, identifier):
    template = loader.get_template('earkcore/ipview.html')

    from config.configuration import django_service_ip
    from config.configuration import django_service_port

    context = RequestContext(request, {
        "django_service_ip": django_service_ip,
        "django_service_port": django_service_port,
        "identifier": identifier,
    })
    return HttpResponse(template.render(context))

@login_required
@csrf_exempt
def check_folder_exists(request, folder):
    path = os.path.join(config_path_work, folder)
    return HttpResponse(str(os.path.exists(path)).lower())

@login_required
@csrf_exempt
def check_identifier_exists(request, identifier):
    try:
        ip = InformationPackage.objects.get(identifier=identifier)
        return HttpResponse("true")
    except:
        return HttpResponse("false")


@login_required
@csrf_exempt
def save_parent_identifier(request, uuid):
    try:
        ip = InformationPackage.objects.get(uuid=uuid)
        if not request.POST.has_key('parent_identifier'):
            return HttpResponse("false")
        else:
            print "PARENT:" + request.POST['parent_identifier']
            ip.parent_identifier = request.POST['parent_identifier']
            ip.save()
            return HttpResponse("true")
    except:
        return HttpResponse("false")


@login_required
@csrf_exempt
def check_submission_exists(request, packagename):
    try:
        ip = InformationPackage.objects.get(packagename=packagename)
        exists = ip and os.path.exists(os.path.join(config_path_work, ip.uuid))
        return HttpResponse(str(exists).lower())
    except:
        return HttpResponse("false")

@login_required
def working_area(request, section, uuid):
    template = loader.get_template('earkcore/workingarea.html')
    request.session['uuid'] = uuid
    r = request.META['HTTP_REFERER']
    title = "SIP to AIP conversion" if "sip2aip" in r else "SIP creation" if "sipcreator" in r else "AIP to DIP conversion"
    section = "sip2aip" if "sip2aip" in r else "sipcreator" if "sipcreator" in r else "aip2dip"
    context = RequestContext(request, {
        "title": title,
        "section": section,
        "uuid": uuid,
        "dirtree": json.dumps(path_to_dict("%s/%s" % (config_path_work, uuid), strip_path_part=config_path_work), indent=4, sort_keys=False, encoding="utf-8")
    })
    return HttpResponse(template.render(context))

@login_required
def xmleditor(request, uuid, ip_xml_file_path):
    try:
        ip_work_dir_sub_path = os.path.join(uuid, ip_xml_file_path)
        abs_xml_file_path = os.path.join(config_path_work, ip_work_dir_sub_path)
        logger.debug("Load file in XML editor: %s" % abs_xml_file_path)
        schema = get_xml_schemalocations(abs_xml_file_path)
        logger.debug(schema)
        template = loader.get_template('earkcore/xmleditor.html')
        note = None
        if ip_xml_file_path.startswith("submission"):
            note = "Overruling storage location: %s" % os.path.join('metadata', ip_xml_file_path)
        def f(x):
            return {
                'sip2aip': "SIP to AIP conversion",
                'sipcreator': "SIP creation",
                'aip2dip': "AIP to DIP conversion",
            }[x]
        context = RequestContext(request, {
            "uuid": uuid,
            "ip_work_dir_sub_path": ip_work_dir_sub_path,
            "ip_xml_file_path": ip_xml_file_path,
            "note": note,
        })
    except XMLSchemaNotFound as err:
        template = loader.get_template('earkcore/error.html')
        tb = traceback.format_exc()
        logging.error(str(tb))
        context = RequestContext(request, {
            "message": str(err.parameter),
            "details": None,
        })
    except Exception, err:
        template = loader.get_template('earkcore/error.html')
        tb = traceback.format_exc()
        logging.error(str(tb))
        context = RequestContext(request, {
            "message": err.message,
            "details": str(tb),
        })
    return HttpResponse(template.render(context))


@login_required
def savexml(request, uuid, ip_xml_file_path):

    # XML code editor changes the attribute to lower case which leads to validation errors
    xml_content = request.body.replace("schemalocation", "schemaLocation")

    result = ip_save_metadata_file.delay(uuid, ip_xml_file_path, xml_content)

    template = loader.get_template('earkcore/xmleditor.html')
    context = RequestContext(request, {

    })
    return HttpResponse()

@login_required
def set_proc_state_valid(request, uuid):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            try:
                job = set_process_state.delay(uuid=uuid, valid=True)
                ip = InformationPackage.objects.get(uuid=uuid)
                ip.statusprocess = 0
                ip.save()
                data = {"success": True, "id": job.id, "uuid": uuid}
            except Exception, err:
                tb = traceback.format_exc()
                logging.error(str(tb))
                data = {"success": False, "errmsg": "Error", "errdetail": str(tb)}
        else:
            data = {"success": False, "errmsg": "not ajax"}
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = {"success": False, "errmsg": err.message, "errdetail": str(tb)}
        return JsonResponse(data)
    return JsonResponse(data)


class SCInformationPackageTable(tables.Table):

    from django_tables2.utils import A
    area = "sipcreator"

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s")
    uuid = tables.LinkColumn('%s:working_area' % area, kwargs={'section': area, 'uuid': A('uuid')})
    packagename = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')})

    class Meta:
        model = InformationPackage
        fields = ('packagename', 'uuid', 'last_change', 'last_task', 'statusprocess')
        attrs = {'class': 'table table-striped table-bordered table-condensed' }
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_statusprocess(value):
        if value == "Success":
            return mark_safe('Success <span class="glyphicon glyphicon-ok-sign" aria-hidden="true" style="color:green"/>')
        elif value == "Error":
            return mark_safe('Error <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true" style="color:#91170A"/>')
        elif value == "Warning":
            return mark_safe('Warning <span class="glyphicon glyphicon-warning-sign" aria-hidden="true" style="color:#F6A50B"/>')
        else:
            return value


@login_required
@csrf_exempt
def read_ipfc(request, ip_sub_file_path):
    # TODO: Direct access to the working area file system is not always possible from the frontent. It is therefore necessary to read the file content from a backend service.
    file_path = os.path.join(config_path_work, ip_sub_file_path)
    logger.debug("Read directory content from directory: " + file_path)
    if not os.path.exists(file_path):
        return HttpResponseNotFound("File not found %s vs %s" % (ip_sub_file_path, file_path))
    elif not os.path.isfile(file_path):
        return HttpResponseBadRequest("Not a file")
    else:
        file_size = fsize(file_path)
        if file_size <= config_max_filesize_viewer:
            mime = get_mime_type(file_path)
            logger.debug("MIME" + mime)
            file_content = read_file_content(file_path)
            return HttpResponse(file_content, content_type=mime)
        else:
            return HttpResponseForbidden("Size of requested file exceeds limit (file size %d > %d)" % (file_size, config_max_filesize_viewer))

@login_required
@csrf_exempt
def access_aip_item(request, identifier, mime, entry):

    mime = mime.strip()
    import re
    def matches(s):
        return re.match("^[a-z]{2,30}/[a-zA-Z0-9-+\.]{2,100}$", s) is not None
    if not matches(mime):
        mime = "application/octet-stream"
        logging.info("warning: using default mime type for access: application/octet-stream")
    logging.debug("Accessing local repository object: %s " % identifier)
    logging.debug("Entry mime-type: %s " % mime)
    logging.debug("entry path: %s " % entry)
    pts = PairtreeStorage(config_path_storage)
    if not pts.identifier_object_exists(identifier):
        return HttpResponseNotFound("Package file for identifier '%s' does not exist" % (identifier))
    else:
        content = pts.get_object_item_stream(identifier, entry)
        return HttpResponse(content, content_type=mime)

@login_required
@csrf_exempt
def get_directory_json(request):
    uuid = request.POST['uuid']
    uuid_work_dir = os.path.join(config_path_work,uuid)
    dirlist = os.listdir(uuid_work_dir)
    if len(dirlist) > 0:
        package_name = dirlist[0]
    else:
        package_name = dirlist
    return JsonResponse({ "data": path_to_dict(uuid_work_dir, strip_path_part=config_path_work+'/'), "check_callback" : "true" })


@login_required
@csrf_exempt
def get_directory_json_remote(request, dir):
    logger.debug("Get directory data: %s" % dir)
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            try:
                job = reception_dir_status.delay(dir)
                data = {"success": True, "id": job.id}
            except Exception, err:
                tb = traceback.format_exc()
                data = {"success": False, "errmsg": "Error", "errdetail": str(tb)}
        else:
            data = {"success": False, "errmsg": "not ajax"}
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = {"success": False, "errmsg": err.message, "errdetail": str(tb)}
        return JsonResponse(data)
    return JsonResponse(data)


@login_required
@csrf_exempt
def poll_state(request):
    """
    @type request: django.core.handlers.wsgi.WSGIRequest
    @param request: Request
    @rtype: django.http.JsonResponse
    @return: JSON response (task state metadata)
    """
    data = {"success": False, "errmsg": "undefined"}
    try:
        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                if task.state == "SUCCESS":
                    data = {"success": True, "state": task.state, "result": task.result}
                else:
                    data = {"success": True, "state": task.state, "info": task.info}
            else:
                data = {"success": False, "errmsg": "No task_id in the request"}
        else:
            data = {"success": False, "errmsg": "Not ajax"}
    except Exception, err:
        data = {"success": False, "errmsg": err.message}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)


@login_required
def reindex_aip_storage(request):
    """
    @type request: django.core.handlers.wsgi.WSGIRequest
    @param request: Request
    @rtype: django.http.JsonResponse
    @return: JSON response (task state metadata)
    """
    data = {"success": False, "errmsg": "undefined"}
    try:
        if request.is_ajax():
            job = index_aip_storage.delay(dir)
            data = {"success": True, "id": job.id}
    except Exception, err:
        data = {"success": False, "errmsg": err.message}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)


@login_required
def start_hdfs_batch_upload(request):
    """
    @type request: django.core.handlers.wsgi.WSGIRequest
    @param request: Request
    @rtype: django.http.JsonResponse
    @return: JSON response (task state metadata)
    """
    data = {"success": False, "errmsg": "undefined"}
    try:
        if request.is_ajax():
            job = hdfs_batch_upload.delay(dir)
            data = {"success": True, "id": job.id}
    except Exception, err:
        data = {"success": False, "errmsg": err.message}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)


@login_required
@csrf_exempt
def solrinterface(request, query):
    from config.configuration import storage_solr_server_ip
    from config.configuration import storage_solr_port
    from config.configuration import storage_solr_core
    query_url = "http://%s:%s/solr/%s/select?%s" % (storage_solr_server_ip, storage_solr_port, storage_solr_core, query)
    logger.debug("SolR query URL: %s" % query_url)
    try:
        response = requests.get(query_url)
        return HttpResponse(response.text, content_type='text/plain')
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        return HttpResponse('{"error": "%s"}' % str(err), content_type='text/plain')
    return data


@login_required
@csrf_exempt
def solrif(request, core, operation):
    logger.debug("SolR query")
    logger.debug("Core: %s" % core)
    logger.debug("Operation: %s" % operation)
    logger.debug("Query: %s" % request.GET.get('q', ''))
    start = request.GET.get('start', '0')
    logger.debug("Start: %s" % start)
    rows = request.GET.get('rows', '20')
    logger.debug("Rows: %s" % rows)
    field_list = request.GET.get('fl', '')
    logger.debug("Field list: %s" % field_list)
    q = urllib.urlencode({'q': request.GET.get('q', ''), "fl": field_list, "start": start, "rows": rows, "wt": "json", "json.wrf": "callback"})

    from config.configuration import storage_solr_server_ip
    from config.configuration import storage_solr_port

    from config.configuration import storage_solr_core
    query_url = "http://%s:%s/solr/%s/%s?%s" % (storage_solr_server_ip, storage_solr_port, storage_solr_core, operation, q)
    logger.debug(query_url)
    data = ""
    try:
        response = requests.get(query_url)
        return HttpResponse(response.text, content_type='text/plain')
    except Exception, err:
        logger.error("error")
        tb = traceback.format_exc()

        logger.error(str(tb))
        data = ""
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = ""
        return HttpResponse(response.text, content_type='text/plain')
    return data


@csrf_exempt
def index_local_storage_ip(request):
    try:
        request_data = json.loads(request.body)
        if request.method == 'POST':
            if 'identifier' in request_data:
                identifier = request_data['identifier']
                job = index_local_storage_ip_func.delay(identifier=identifier)

                # 201 Created
                return JsonResponse({"success": True, "jobid": job.id, "identifier": identifier, "message": "Indexing job submitted successfully."}, status=201)
            else:
                # 400 Bad Request
                return JsonResponse({"success": False, "message": "Required POST parameter 'identifier' missing."}, status=400)
        else:
            # 400 Bad Request
            return JsonResponse({"success": False, "message": "Only POST request allowed"}, status=400)
    except ObjectDoesNotExist:
        # 404 Not Found
        return JsonResponse({"success": False, "message": "The process ID cannot be found"}, status=404)
    except ValueError:
        # 400 Bad Request
        return JsonResponse({"success": False, "message": "Bad request: error parsing request body data."}, status=400)
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        # 500 Internal Server Error
        return JsonResponse({"success": False, "message": "An error occurred: %s" % err.message}, status=500)


@csrf_exempt
def add_premis_event_ip(request):
    try:
        request_data = json.loads(request.body)
        if request.method == 'POST':
            if 'uuid' in request_data:
                uuid = request_data['uuid']
                outcome = request_data['outcome']
                task_name = request_data['task_name']
                event_type = request_data['event_type']
                linked_object = request_data['linked_object']
                job = add_premis_event_ip_func.delay(uuid=uuid, outcome=outcome, task_name=task_name, event_type=event_type, linked_object=linked_object)
                # 201 Created
                return JsonResponse({"success": True, "jobid": job.id, "uuid": uuid, "message": "Adding PREMIS event operation submitted successfully."}, status=201)
            else:
                # 400 Bad Request
                return JsonResponse({"success": False, "message": "Required POST parameter 'identifier' missing."}, status=400)
        else:
            # 400 Bad Request
            return JsonResponse({"success": False, "message": "Only POST request allowed"}, status=400)
    except ObjectDoesNotExist:
        # 404 Not Found
        return JsonResponse({"success": False, "message": "The process ID cannot be found"}, status=404)
    except ValueError:
        # 400 Bad Request
        return JsonResponse({"success": False, "message": "Bad request: error parsing request body data."}, status=400)
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        # 500 Internal Server Error
        return JsonResponse({"success": False, "message": "An error occurred: %s" % err.message}, status=500)
