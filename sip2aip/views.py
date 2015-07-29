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

from earkcore.models import InformationPackage

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
        return context