import functools
import json
import logging
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
from workflow.models import WorkflowModules

@login_required
def index(request):
    template = loader.get_template('sip2aip/index.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

class InformationPackageList(ListView):
    """
    List IngestQueue
    """
    model = InformationPackage
    template_name='sip2aip/reception.html'
    context_object_name='ips'
    queryset=InformationPackage.objects.all()

    def dispatch(self, *args, **kwargs):
        return super(InformationPackageList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InformationPackageList, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context

class InformationPackageDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = InformationPackage
    context_object_name='ip'
    template_name='sip2aip/detail.html'


    def dispatch(self, *args, **kwargs):
        return super(InformationPackageDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InformationPackageDetail, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        context['form'] = forms.WorkflowModuleSelectForm()
        return context

@login_required
def progress(request):
    if 'task_id' in request.session.keys() and request.session['task_id']:
        task_id = request.session['task_id']
    context = RequestContext(request, {
        'form': forms.PackageWorkflowModuleSelectForm()
    })
    return render_to_response('sip2aip/progress.html', locals(), context_instance=context)

@login_required
@csrf_exempt
def apply_task(request):
    data = {}
    try:
        selected_ip = request.GET['selected_ip']
        print "selected_ip: " + request.GET['selected_ip']
        selected_action = request.GET['selected_action']
        print "selected_action: " + request.GET['selected_action']
        if not (selected_ip and selected_action):
            return JsonResponse({"error": "Input parameters missing!"})
        wfm = WorkflowModules.objects.get(pk=selected_action)
        if request.is_ajax():
            taskClass = getattr(tasks, wfm.identifier)
            job = taskClass().apply_async((selected_ip,), queue='default')
            request.session['task_id'] = job.id
            data = {"id": job.id}
        else:
            data = {"error": "Not ajax"}
    except:
         tb = traceback.format_exc()
         print str(tb)
         return JsonResponse({"error": "an error occurred!"})
    return JsonResponse(data)

@login_required
@csrf_exempt
def poll_state(request):
    try:
        data = {}
        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                data = {"result": task.result.success, "state": task.state}
            else:
                data = {"error": "No task_id in the request"}
        else:
            data = {"error": "Not ajax"}
    except Exception, err:
            print err

    return JsonResponse(data)
