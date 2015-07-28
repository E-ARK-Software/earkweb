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

from earkcore.models import InformationPackage

@login_required
def index(request):
    template = loader.get_template('sip2aip/index.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
def reception(request):
    information_packages = InformationPackage.objects.all()
    template = loader.get_template('sip2aip/reception.html')
    context = RequestContext(request, {'ips': information_packages})
    return HttpResponse(template.render(context))