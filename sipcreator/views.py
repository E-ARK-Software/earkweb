import os
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from earkcore.packaging.extraction import Extraction
from forms import TinyUploadFileForm
from config.params import config_path_work
from earkcore.utils.stringutils import safe_path_string
from earkcore.utils.fileutils import mkdir_p
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from earkcore.models import InformationPackage
from earkcore.utils.randomutils import getUniqueID
from earkcore.utils.fileutils import rmtree

from earkcore.models import StatusProcess_CHOICES
from sip2aip.forms import SIPCreationPackageWorkflowModuleSelectForm
import json
from earkcore.filesystem.fsinfo import path_to_dict
from workers.tasks import extract_and_remove_package

@login_required
def index(request):
    template = loader.get_template('sipcreator/index.html')
    ulform = TinyUploadFileForm()
    ulform.form_show_labels = False
    uuid = ""
    packagename = ""
    if 'uuid' in request.session:
        uuid = request.session['uuid']
    if 'packagename' in request.session:
        packagename = request.session['packagename']
    print "uuid: "+uuid
    print "packagename: "+packagename
    context = RequestContext(request, {
        'uploadFileForm': ulform,
        'uuid': uuid,
        'packagename': packagename,
    })
    return HttpResponse(template.render(context))

@login_required
def sipcreation(request):
    template = loader.get_template('sipcreator/sipcreation.html')
    uuid = ""
    packagename = ""
    ip = None
    if 'uuid' in request.session:
        uuid = request.session['uuid']
        ip = InformationPackage.objects.get(uuid=uuid)
    if 'packagename' in request.session:
        packagename = request.session['packagename']
    form = SIPCreationPackageWorkflowModuleSelectForm()
    context = RequestContext(request, {
        "ip": ip,
        "StatusProcess_CHOICES": dict(StatusProcess_CHOICES),
        "config_path_work": config_path_work,
        'uuid': uuid,
        'packagename': packagename,
        'form': form
    })
    return HttpResponse(template.render(context))

@login_required
def add_file(request, uuid, folder):
    work_dir = os.path.join(config_path_work,uuid)
    folder_path = os.path.join(config_path_work,uuid,folder)
    if not os.path.exists(folder_path):
        mkdir_p(folder_path)
    if request.method == 'POST':
        form = TinyUploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_aip(work_dir, folder, request.FILES['content_file'])
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))

        url = reverse('sipcreator:index')
        return HttpResponseRedirect(url)
    else:
        pass

def upload_aip(work_dir, folder, f):
    folder_path = os.path.join(work_dir, folder)
    print "Upload file '%s' to working directory: %s" % (f, folder)
    if not os.path.exists(folder_path):
        mkdir_p(folder_path)
    destination_file = os.path.join(folder_path,f.name)
    with open(destination_file, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()
    if f.name.endswith(".tar"):
        async_res = extract_and_remove_package.delay(destination_file, folder_path, os.path.join(work_dir, 'metadata/sip_creation.log'))
        print "Package extraction task '%s' to extract package '%s' to working directory: %s" % (async_res.id, f.name, folder)

@login_required
@csrf_exempt
def initialize(request, packagename):
    uuid = getUniqueID()
    request.session['uuid'] = uuid
    request.session['packagename'] = packagename
    sip_struct_work_dir = os.path.join(config_path_work,uuid)
    print "package name: %s" % packagename
    print "working directory: %s" % sip_struct_work_dir

    print "uuid (session): %s" % request.session['uuid']
    print "package name (session): %s" % request.session['packagename']
    mkdir_p(os.path.join(sip_struct_work_dir, 'data/content'))
    mkdir_p(os.path.join(sip_struct_work_dir, 'data/documentation'))
    mkdir_p(os.path.join(sip_struct_work_dir, 'metadata'))
    InformationPackage.objects.create(path=os.path.join(config_path_work, uuid), uuid=uuid, statusprocess=10, packagename=packagename)
    return HttpResponse(str(True).lower())

@login_required
def working_area(request, uuid):
    template = loader.get_template('sipcreator/workingarea.html')
    print uuid
    context = RequestContext(request, {
        "uuid": uuid,
        "dirtree": json.dumps(path_to_dict('/var/data/earkweb/work/'+uuid), indent=4, sort_keys=False, encoding="utf-8")
    })
    return HttpResponse(template.render(context))

@login_required
def delete(request, uuid):
    template = loader.get_template('sipcreator/deleted.html')
    del request.session['uuid']
    del request.session['packagename']
    if uuid:
        rmtree(os.path.join(config_path_work, uuid))
    context = RequestContext(request, {
        'uuid': uuid,
    })
    return HttpResponse(template.render(context))