import os
import functools
import json
import tarfile
from threading import Thread
import traceback
import urllib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext, loader
from django.utils import timezone
from lxml import etree
import requests
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.contrib.auth.decorators import permission_required, login_required
from earkcore.models import StatusProcess_CHOICES
from django.views.decorators.csrf import csrf_exempt

from earkcore.models import InformationPackage

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from celery.result import AsyncResult
from workers import tasks
from django.http import JsonResponse
from django.forms import ModelChoiceField
from sip2aip import forms
import urllib2
import workers.tasks
from workers.taskconfig import TaskConfig
from workflow.models import WorkflowModules
import json

from config.params import config_path_work
from earkcore.filesystem.fsinfo import path_to_dict

import logging

@login_required
def index(request):
    print request.user
    template = loader.get_template('workflow/index.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))

@login_required
def workflow_language(request):
    print request.user
    wfdefs = WorkflowModules.objects.all()
    template = loader.get_template('workflow/language.js')
    context = RequestContext(request, {
        'workflow_definitions': wfdefs
    })
    return HttpResponse(template.render(context), content_type='text/plain; charset=utf8')

@login_required
def backend(request):
    """
    Backend of the wiring editor for handling POST requests.
    Methods are 'listWirings', 'saveWiring', 'deleteWiring'.
    :param request: Request
    :return: HttpResponse(status=200, "OK")
    """
    if request.method == "POST":

        try:
            data = json.loads(str(request.body))
            logging.debug("Request (JSON):\n" + json.dumps(data, indent=2))
            if data['method'] == "listWirings":
                wirings = Wirings.objects.all()
                wiringJsons = []
                # each wiring (wiring.working) is returned as a backslash escaped string (substitution variable: working),
                # therefore double quotes in "wiring.working" are backslash escaped.
                for wiring in wirings:
                    wiringJsons.append("""{ "id": "%(id)s", "name": "%(name)s", "working": "%(working)s", "language": "%(language)s" }"""
                                       % { 'name': wiring.name, 'working': (wiring.working).replace('"', '\\"'), 'language': wiring.language, 'id': wiring.id })
                jsonStr = """{"id": 1, "result": [ %(modules)s ], "error": null }""" % { 'modules': (",".join(wiringJsons)) }
                jsonObj = json.loads(jsonStr)
                logging.debug("Response (JSON):\n" + json.dumps(jsonObj, indent=2))
                return HttpResponse(jsonStr)
            if data['method'] == "saveWiring":
                name = data['params']['name']
                working = data['params']['working']
                language = data['params']['language']
                wiring = Wirings.objects.create(language=language,name=name,working=working)
                wiring.save()
            if data['method'] == "deleteWiring":
                name = data['params']['name']
                logging.debug("Delete wiring: %s" % name)
                u = Wirings.objects.get(name=name).delete()
        except Exception:
            logging.error('test', exc_info=True)
        return HttpResponse(status=200)
    else:
        pass

@login_required
def execution(request):
    if 'task_id' in request.session.keys() and request.session['task_id']:
        task_id = request.session['task_id']
    context = RequestContext(request, {
        'form': forms.PackageWorkflowModuleSelectForm()
    })
    return render_to_response('workflow/execution.html', locals(), context_instance=context)

@login_required
@csrf_exempt
def apply_workflow(request):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        print "Workflow execution"
        # selected_ip = request.POST['selected_ip']
        # print "selected_ip: " + request.POST['selected_ip']
        # selected_action = request.POST['selected_action']
        # print "selected_action: " + request.POST['selected_action']
        # if not (selected_ip and selected_action):
        #     return JsonResponse({"success": False, "errmsg": "Missing input parameter!"})
        # wfm = WorkflowModules.objects.get(pk=selected_action)
        # tc = TaskConfig(wfm.expected_status,  wfm.success_status, wfm.error_status)
        # if request.is_ajax():
        #     taskClass = getattr(tasks, wfm.identifier)
        #     print "Executing task: %s" % wfm.identifier
        #     job = taskClass().apply_async((selected_ip, tc,), queue='default')
        #     print "Task identifier: %s" % job.id
        #     data = {"success": True, "id": job.id}
        # else:
        #     data = {"success": False, "errmsg": "not ajax"}
        data = {"success": True, "id": "xyz", "myprop": "val"}
    except:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = {"success": False, "errmsg": "an error occurred!"}
        return JsonResponse(data)
    return JsonResponse(data)


@login_required
@csrf_exempt
def apply_task(request):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        selected_ip = request.POST['selected_ip']
        print "selected_ip: " + request.POST['selected_ip']
        selected_action = request.POST['selected_action']
        print "selected_action: " + request.POST['selected_action']
        if not (selected_ip and selected_action):
            return JsonResponse({"success": False, "errmsg": "Missing input parameter!"})
        wfm = WorkflowModules.objects.get(pk=selected_action)
        tc = TaskConfig(wfm.expected_status,  wfm.success_status, wfm.error_status)
        if request.is_ajax():
            try:
                taskClass = getattr(tasks, wfm.identifier)
                print "Executing task: %s" % wfm.identifier
                job = taskClass().apply_async((selected_ip, tc,), queue='default')
                print "Task identifier: %s" % job.id
                data = {"success": True, "id": job.id}
            except AttributeError, err:
                errdetail = """The workflow module '%s' does not exist.
It might be necessary to run 'python ./workers/scantasks.py' to register new or renamed tasks.""" % wfm.identifier
                data = {"success": False, "errmsg": "Workflow module '%s' does not exist" % wfm.identifier, "errdetail": errdetail}
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
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                if task.state == "SUCCESS":
                    aggr_log = '\n'.join(task.result.log)
                    aggr_err = '\n'.join(task.result.err)
                    data = {"success": True, "result": task.result.success, "state": task.state, "log": aggr_log, "err": aggr_err}
                elif task.state == "PROGRESS":
                    data = {"success": True, "result": task.state, "state": task.state, "info": task.info}
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
@csrf_exempt
def get_directory_json(request):
    uuid = request.POST['uuid']
    package_name = os.listdir('/var/data/earkweb/work/'+uuid+'/')[0]
    return JsonResponse({ "data": path_to_dict('/var/data/earkweb/work/'+uuid+'/'+package_name) })