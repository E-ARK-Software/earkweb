import os
import traceback
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
import logging
logger = logging.getLogger(__name__)
from .forms import UploadCtrlFile
import subprocess32
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
                args = ['hadoop', 'jar', '/opt/ToMaR/target/tomar-2.0.0-SNAPSHOT-jar-with-dependencies.jar',
                        '-r', '/user/janrn/tomarspecs', '-i', '%s', '-o', '/user/janrn/output-ner', '-n', '1'] % tomarctrl
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
