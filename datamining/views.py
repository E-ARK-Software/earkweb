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
# from config.params import config_path_work, config_path_reception
import logging
logger = logging.getLogger(__name__)
from operator import itemgetter, attrgetter, methodcaller
from earkcore.utils.fileutils import mkdir_p
from django.core.urlresolvers import reverse
from workers.tasks import LilyHDFSUpload
from .forms import SolrQuery, NERSelect, CSelect
from sandbox.datamining.dm_start import dm_start
@login_required
@csrf_exempt


@login_required
def start(request):
    template = loader.get_template('datamining/start.html')
    solr_query_form = SolrQuery()
    ner_model_select = NERSelect()
    categoriser_select = CSelect()
    context = RequestContext(request, {
        'solr_query_form': solr_query_form,
        'ner_model_select': ner_model_select,
        'categoriser_select': categoriser_select
    })
    return HttpResponse(template.render(context))


@login_required
def celery_nlp(request):
    if request.method == 'POST':
        # TODO: feedback
        # template = loader.get_template('datamining/start.html')
        try:
            print request.POST
            # package_id = request.POST['package_id']
            # print package_id
            # ctrlfile = request.FILES['ctrl_file']
            # tomarctrl = ctrlToHDFS(ctrlfile)
            #
            # if tomarctrl is not False:
            #     args = ['hadoop', 'jar', 'tomar-2.0.0-SNAPSHOT-jar-with-dependencies.jar',
            #             '-r', 'tomarspecs', '-i', '%s', '-o', 'output-ner', '-n', '1'] % tomarctrl
            #     subprocess32.Popen(args)
            #
            #     context = RequestContext(request, {
            #         'status': 'LAUNCHED'
            #     })
            # else:
            #     context = RequestContext(request, {
            #         'status': 'Upload of control file failed.'
            #     })
        except Exception, e:
            # # return error message
            # context = RequestContext(request, {
            #     'status': 'ERROR: %s' % e.message
            # })
            pass
    # else:
    #     template = loader.get_template('datamining/start.html')
    #     context = RequestContext(request, {
    #
    #     })
    # return HttpResponse(template.render(context))

