import os
import traceback
from django.template import loader
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.contrib.auth.decorators import login_required
from earkcore.models import StatusProcess_CHOICES
from earkcore.models import InformationPackage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
from earkcore.utils.randomutils import getUniqueID
from sip2aip.forms import UploadSIPDeliveryForm
from sipcreator.forms import TinyUploadFileForm
from workers import tasks
from django.http import JsonResponse
from sip2aip import forms
from workers.ip_state import IpState
from workers.taskconfig import TaskConfig
from workers.tasks import SIPtoAIPReset
from workflow.models import WorkflowModules
from config.params import config_path_work, config_path_reception
import logging
logger = logging.getLogger(__name__)
from operator import itemgetter, attrgetter, methodcaller
from earkcore.utils.fileutils import mkdir_p
from django.core.urlresolvers import reverse
from workers.tasks import LilyHDFSUpload
from django.views.generic import FormView
#from .forms import MRJobSelectForm
#from .models import PostAd
from .models import JobSelect, JOBS
@login_required
@csrf_exempt

@login_required
def start(request):
    template = loader.get_template('mrinterface/start.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))
    # return HttpResponse("Hello world.")

# class PostAdPage(FormView):
#     template_name = 'earkweb/start.html'
#     success_url = '/awesome/'
#     form_class = MRJobSelectForm
#
#     def form_valid(self, form):
#         return HttpResponse('Works.')