from django.template import RequestContext, loader
from django.http import HttpResponse
import urllib
import json

import requests
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from django.shortcuts import render

from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    print request.user
    template = loader.get_template('workflow/index.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))