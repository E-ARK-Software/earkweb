import json
import re

from eatb.storage.directorypairtreestorage import make_storage_data_directory_path
from eatb.utils.datetime import get_date_from_iso_str, DT_ISO_FORMAT
from eatb.utils.fileutils import path_to_dict

from config.configuration import sw_version, django_backend_service_api_url
from config.configuration import sw_version_date

from django.shortcuts import redirect
from django.utils import translation
from django.views.generic.base import View
from django.conf import settings
import os
import traceback
import logging
from urllib.parse import urlencode

import requests
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
from django.http import JsonResponse
from celery.result import AsyncResult

from config.configuration import config_path_work, config_path_storage, django_backend_service_host, \
    django_backend_service_port, verify_certificate
from earkweb.models import InformationPackage
from util.djangoutils import get_user_api_token
from django.utils.translation import gettext as trans
logger = logging.getLogger(__name__)


class ActivateLanguageView(View):
    language_code = ''
    redirect_to = ''

    def get(self, request, *args, **kwargs):
        self.redirect_to = request.META.get('HTTP_REFERER')
        self.language_code = kwargs.get('language_code')
        translation.activate(self.language_code)
        request.session[translation.LANGUAGE_SESSION_KEY] = self.language_code
        response = redirect(request.META.get('HTTP_REFERER', request.path_info))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, self.language_code)
        return response


@login_required
def home(request):
    template = loader.get_template('earkweb/home.html')
    context = {
        'sw_version': sw_version,
        'sw_version_date': sw_version_date
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def version(request):
    template = loader.get_template('earkweb/version.html')
    context = {

    }
    return HttpResponse(template.render(context=context, request=request))


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
def check_submission_exists(request, package_name):
    try:
        ip = InformationPackage.objects.get(package_name=package_name)
        exists = ip and os.path.exists(os.path.join(config_path_work, ip.process_id))
        return HttpResponse(str(exists).lower())
    except:
        return HttpResponse("false")


def working_area2(request, section, process_id):
    template = loader.get_template('earkweb/workingarea2.html')
    request.session['process_id'] = process_id
    r = request.META['PATH_INFO']
    title = trans("Information package management") if "management" in r else trans("Submission") if "submission" in r else trans("Access")
    section = "management" if "management" in r else "submission" if "submission" in r else "access"
    url = "/earkweb/api/informationpackages/%s/dir-json" % (process_id)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    context = {
        "title": title,
        "section": section,
        "process_id": process_id,
        "dirasjson": response.content.decode('utf-8'),
        "django_backend_service_api_url": django_backend_service_api_url
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def storage_area(request, section, identifier):
    template = loader.get_template('earkweb/workingarea2.html')
    request.session['identifier'] = identifier
    r = request.META['HTTP_REFERER']
    title = "Information package management" if "management" in r else "Submission" if "submission" in r else "Access"
    section = "management" if "management" in r else "submission" if "submission" in r else "access"
    #store_path = "%s" % make_storage_data_directory_path(identifier, config_path_storage)
    #logger.info(store_path)
    url = "/earkweb/api/storage/informationpackages/%s/dir-json" % (identifier)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)

    inventory_url = "/earkweb/api/informationpackages/%s/file-resource/inventory.json" % (
    identifier)
    print(inventory_url)
    inventory_response = requests.get(inventory_url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    inventory = json.loads(inventory_response.text)

    version_timeline_data = [
        {"id": re.sub("\D", "", key),
         "content": "%s (%s)" % (val["message"], key),
         "start": val["created"],
        "className" : "myClassName"
         }
        for key, val in inventory["versions"].items()]

    times = [val["created"] for key, val in inventory["versions"].items()]
    times.sort()
    print(times)
    if len(times) > 1:
        min_dtstr = times[0]
        max_dtstr = times[len(times)-1]
        min_dt = get_date_from_iso_str(min_dtstr, DT_ISO_FORMAT)
        max_dt = get_date_from_iso_str(max_dtstr, DT_ISO_FORMAT)
        delta =  max_dt - min_dt
        print(delta.seconds)
        scale = ("seconds", (delta.seconds)) if delta.seconds < 60 \
            else ("minutes", int(delta.seconds/60)) if delta.seconds < 3600 \
            else ("hours", int(delta.seconds/3600)) if delta.seconds < 86400 \
            else ("days", (delta.days)) if delta.seconds < 2592000 \
            else ("months", int(delta.days/30)) if delta.seconds < 31536000 \
            else ("years", int(delta.days/365))
        scale_unit, scale_value = scale
    else:
        min_dtstr = max_dtstr = times[0]
        scale_unit = "days"
        scale_value = "3"

    context = {
        "title": title,
        "section": section,
        "process_id": identifier,
        "dirasjson": response.content.decode('utf-8'),
        "show_timeline": True,
        "identifier": identifier,
        "version_timeline_data": version_timeline_data,
        "scale_unit": scale_unit,
        "scale_value": (scale_value*10),
        "min_dt": min_dtstr,
        "max_dt": max_dtstr
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def read_file(request, ip_sub_file_path, area=None):
    """
    :param request: Request
    :param ip_sub_file_path: path to be read from working directory
    :return: HTTP response (content and content type)
    """
    parts = ip_sub_file_path.split("/")
    process_id = parts[0]
    path = ip_sub_file_path.lstrip(parts[0]).lstrip("/")
    area = area if area else "informationpackages"
    url = "/earkweb/api/%s/%s/file-resource/%s/" % (area, process_id, path)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    content_type = response.headers['content-type']
    return HttpResponse(response.content, content_type=content_type)


@login_required
@csrf_exempt
def get_directory_json(request):
    process_id = request.POST['process_id']
    work_dir = os.path.join(config_path_work, process_id)
    dirlist = os.listdir(work_dir)
    if len(dirlist) > 0:
        package_name = dirlist[0]
    else:
        package_name = dirlist
    return JsonResponse({ "data": path_to_dict(work_dir, strip_path_part=config_path_work+'/'), "check_callback": "true"})


@login_required
@csrf_exempt
def get_storage_directory_json(request):
    identifier = request.POST['identifier']
    storage_dir = make_storage_data_directory_path(identifier, config_path_storage)
    dirlist = os.listdir(storage_dir)
    if len(dirlist) > 0:
        package_name = dirlist[0]
    else:
        package_name = dirlist
    return JsonResponse({"data": path_to_dict(storage_dir, strip_path_part=config_path_storage+'/'), "check_callback": "true"})


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
    except Exception as err:
        data = {"success": False, "errmsg": err.message}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)


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
    q = urlencode({'q': request.GET.get('q', ''), "fl": field_list, "start": start, "rows": rows, "wt": "json", "json.wrf": "callback"})

    from config.configuration import solr_host
    from config.configuration import solr_port

    from config.configuration import solr_core
    query_url = "http://%s:%s/solr/%s/%s?%s" % (solr_host, solr_port, solr_core, operation, q)
    logger.debug(query_url)
    data = ""
    try:
        response = requests.get(query_url, verify=verify_certificate)
        return HttpResponse(response.text, content_type='application/javascript; charset=utf-8')
    except Exception as err:
        logger.error("error")
        tb = traceback.format_exc()

        logger.error(str(tb))
        data = ""
    except Exception as err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = ""
        return HttpResponse(response.text, content_type='text/plain')
    return data

