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
from .forms import UploadCtrlFile
import subprocess32
from earkcore.process.cli.CliCommand import CliCommand
@login_required
@csrf_exempt

@login_required
def start(request):
    template = loader.get_template('mrinterface/start.html')
    ctrl_file_upload = UploadCtrlFile()
    context = RequestContext(request, {
        'ctrl_file_upload': ctrl_file_upload
    })
    return HttpResponse(template.render(context))

@login_required
def launchmr(request):
    if request.method == 'POST':
        # TODO: different feedback for successful job launch and errors
        template = loader.get_template('mrinterface/feedback.html')
        # launch the mr job
        # TODO: create the ctrl file from HTML form
        try:
            ctrlfile = request.FILES['ctrl_file']
            tomarctrl = ctrlToHDFS(ctrlfile)

            if tomarctrl is not False:
                args = ['hadoop', 'jar', 'tomar-2.0.0-SNAPSHOT-jar-with-dependencies.jar',
                        '-r', 'tomarspecs', '-i', '%s', '-o', 'output-ner', '-n', '1'] % tomarctrl
                subprocess32.Popen(args)

                context = RequestContext(request, {
                    'status': 'LAUNCHED'
                })
            else:
                context = RequestContext(request, {
                    'status': 'Upload of control file failed.'
                })
        except Exception, e:
            # return error message
            context = RequestContext(request, {
                'status': 'ERROR: %s' % e.message
            })
            pass
    else:
        template = loader.get_template('mrinterface/feedback.html')
        context = RequestContext(request, {

        })
    return HttpResponse(template.render(context))


def ctrlToHDFS(ctrl_file):
    try:
        destination_file = os.path.join('/tmp', ctrl_file.name)
        with open(destination_file, 'wb+') as destination:
            for chunk in ctrl_file.chunks():
                destination.write(chunk)
        destination.close()
        # copy to HDFS
        args = ['hadoop', 'fs', '-put', '%s' % destination_file]
        filetohdfs = subprocess32.Popen(args)
        filetohdfs.wait()
        os.remove(destination_file)     # remove ctrl file from server
        return destination_file
    except Exception, e:
        print e
        return False
