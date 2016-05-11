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
from subprocess32 import Popen, PIPE
import requests
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
            upload = ctrlToHDFS(ctrlfile)

            if upload is False:
                context = RequestContext(request, {
                    'status': 'Upload of control file failed.'
                })
            else:
                hdfs_ctrl = os.path.join('/user/eark/data', upload)

                # workaround: move ctrl file to hdfs:///tmp, to be able to create the 'rearranged' file independent of active user
                mvargs = ['hadoop', 'fs', '-mv', hdfs_ctrl, '/tmp']
                mvcmd = Popen(mvargs)
                mvcmd.wait()

                tmp_ctrl = os.path.join('/tmp', ctrlfile.name)
                args = ['hadoop', 'jar', '/opt/ToMaR/target/tomar-2.0.0-SNAPSHOT-jar-with-dependencies.jar',
                        '-r', '/user/janrn/tomarspecs', '-i', tmp_ctrl, '-o', '/user/janrn/output-ner', '-n', '1']
                mrcmd = Popen(args, stdout=PIPE, stderr=PIPE)
                output, error_output = mrcmd.communicate()

                context = RequestContext(request, {
                    'status': 'LAUNCHED, output: %s \nerrors: %s' % (output, error_output)
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


SERVER_PROTOCOL_PREFIX = 'http://'
SERVER_NAME = '81.189.135.189/dm-hdfs-storage'
SERVER_HDFS = SERVER_PROTOCOL_PREFIX + SERVER_NAME + '/hsink/fileresource'
FILE_RESOURCE = SERVER_HDFS + '/files/{0}'

def ctrlToHDFS(ctrl_file):
    try:
        upload_destination = os.path.join('/tmp', ctrl_file.name)
        with open(upload_destination, 'wb+') as destination:
            for chunk in ctrl_file.chunks():
                destination.write(chunk)
        destination.close()

        # copy to HDFS
        with open(upload_destination, 'r') as f:
            filename = upload_destination.rpartition('/')[2]
            r = requests.put(FILE_RESOURCE.format(filename), data=f)
            os.remove(upload_destination)  # remove ctrl file from server
            if r.status_code == 201:
                return r.headers['location'].rpartition('/files/')[2]
            else:
                return False
    except Exception, e:
        print e
        return False
