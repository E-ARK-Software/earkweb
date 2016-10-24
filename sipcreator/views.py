import logging
logger = logging.getLogger(__name__)
import os
import shutil
from celery.result import AsyncResult
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from config.configuration import root_dir
from config.configuration import flower_server
from config.configuration import flower_port
from config.configuration import flower_path
from earkcore.packaging.untar import Untar
from forms import TinyUploadFileForm
from forms import UploadFileForm
from config.configuration import config_path_work
from earkcore.utils.stringutils import safe_path_string, whitespace_separated_text_to_dict
from earkcore.utils.fileutils import mkdir_p, copy_tree_content
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from earkcore.models import InformationPackage
from earkcore.utils.randomutils import getUniqueID
from earkcore.utils.fileutils import rmtree
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from earkcore.models import StatusProcess_CHOICES
from sip2aip.forms import SIPCreationPackageWorkflowModuleSelectForm
import json
from earkcore.filesystem.fsinfo import path_to_dict
from workers.tasks import extract_and_remove_package, SIPReset, run_sipcreation_batch
from workflow.models import WorkflowModules
from django.shortcuts import render_to_response
from workers.ip_state import IpState
import traceback
import re
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig


@login_required
@csrf_exempt
def ip_detail_table(request):
    pkg_id = request.POST['pkg_id']
    print pkg_id
    print config_path_work
    context = RequestContext(request, {
        "ip": InformationPackage.objects.get(pk=pkg_id),
        "StatusProcess_CHOICES": dict(StatusProcess_CHOICES),
        "config_path_work": config_path_work
    })
    return render_to_response('sipcreator/iptable.html', locals(), context_instance=context)


@login_required
def start(request):
    template = loader.get_template('sipcreator/start.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))



class InformationPackageTable(tables.Table):

    from django_tables2.utils import A
    area = "sipcreator"

    last_task = tables.Column(verbose_name='Last task')
    statusprocess = tables.Column(verbose_name='Outcome' )
    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name= 'Last change')
    uuid = tables.LinkColumn('%s:working_area' % area, kwargs={'section': area, 'uuid': A('uuid')}, verbose_name= 'Process ID')
    packagename = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name= 'Package name')

    class Meta:
        model = InformationPackage
        fields = ('packagename', 'uuid', 'last_change', 'last_task', 'statusprocess')
        attrs = {'class': 'table table-striped table-bordered table-condensed' }
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_statusprocess(value):
        if value == "Success":
            return mark_safe('Success <span class="glyphicon glyphicon-ok-sign" aria-hidden="true" style="color:green"/>')
        elif value == "Error":
            return mark_safe('Error <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true" style="color:#91170A"/>')
        elif value == "Warning":
            return mark_safe('Warning <span class="glyphicon glyphicon-warning-sign" aria-hidden="true" style="color:#F6A50B"/>')
        else:
            return value


@login_required
@csrf_exempt
def informationpackages_overview(request):
    area = "sipcreator"
    areacode = "1"
    filterword = request.POST['filterword'] if 'filterword' in request.POST.keys() else ""
    sql_query = """
    select ip.id as id, ip.path as path, ip.statusprocess as statusprocess, ip.uuid as uuid, ip.packagename as packagename, ip.identifier as identifier
    from workflow_workflowmodules as wf
    inner join earkcore_informationpackage as ip
    on wf.identifier=ip.last_task_id
    where wf.tstage & {1} and (ip.uuid like '%%{0}%%' or ip.packagename like '%%{0}%%' or ip.identifier like '%%{0}%%')
    order by ip.last_change desc;
    """.format(filterword, areacode)
    queryset = InformationPackage.objects.raw(sql_query)
    table = InformationPackageTable(queryset)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    context = RequestContext(request, {
        'informationpackage': table,
    })
    if request.method == "POST":
        return render_to_response('earkcore/ipstable.html', locals(), context_instance=context)
    else:
        return render(request, '%s/overview.html' % area, {'informationpackage': table})


class HelpProcessingStatus(ListView):
    """
    Processing status
    """
    model = WorkflowModules
    template_name = 'sipcreator/help_processing_status.html'
    context_object_name = 'wfms'

    queryset=WorkflowModules.objects.extra(where=["ttype & %d" % 1]).order_by('ordval')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HelpProcessingStatus, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HelpProcessingStatus, self).get_context_data(**kwargs)
        return context


# class InformationPackageDetail(DetailView):
#     """
#     Information Package Detail View
#     """
#     model = InformationPackage
#     context_object_name='ip'
#     template_name='sipcreator/detail.html'
#
#     @method_decorator(login_required)
#     def dispatch(self, *args, **kwargs):
#         return super(InformationPackageDetail, self).dispatch( *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super(InformationPackageDetail, self).get_context_data(**kwargs)
#         context['StatusProcess_CHOICES'] =  dict(StatusProcess_CHOICES)
#         context['config_path_work'] = config_path_work
#         uploadFileForm = TinyUploadFileForm()
#         context['uploadFileForm'] = uploadFileForm
#         context['repr_dirs'] =
#         return context

@login_required
def sip_detail_rep(request, pk, rep):
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('sipcreator/detail.html')
    upload_file_form = TinyUploadFileForm()
    repr_dir = os.path.join(ip.path,"representations")
    repr_dirs = filter(lambda x: os.path.isdir(os.path.join(repr_dir, x)), os.listdir(repr_dir))

    request.session['rep'] = rep

    context = RequestContext(request, {
        'uuid': ip.uuid,
        'StatusProcess_CHOICES': dict(StatusProcess_CHOICES),
        'config_path_work': config_path_work,
        'uploadFileForm': upload_file_form,
        'repr_dirs': repr_dirs,
        'ip': ip,
        'rep': rep,
        'pk': pk,
    })
    return HttpResponse(template.render(context))

@login_required
def sip_detail(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('sipcreator/detail.html')
    upload_file_form = TinyUploadFileForm()
    repr_dir = os.path.join(ip.path,"representations")

    repr_dirs = [] if not os.path.exists(repr_dir) else filter(lambda x: os.path.isdir(os.path.join(repr_dir, x)), os.listdir(repr_dir))

    rep = "" if len(repr_dirs) == 0 else repr_dirs[0]
    request.session['rep'] = rep

    context = RequestContext(request, {
        'uuid': ip.uuid,
        'StatusProcess_CHOICES': dict(StatusProcess_CHOICES),
        'config_path_work': config_path_work,
        'uploadFileForm': upload_file_form,
        'repr_dirs': repr_dirs,
        'ip': ip,
        'rep': rep,
        'pk': pk,
    })
    return HttpResponse(template.render(context))

class SIPCreationDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = InformationPackage
    context_object_name='ip'
    template_name='sipcreator/sipcreation.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SIPCreationDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SIPCreationDetail, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] =  dict(StatusProcess_CHOICES)
        context['config_path_work'] = config_path_work
        form = SIPCreationPackageWorkflowModuleSelectForm()
        context['form'] = form
        return context

@login_required
@csrf_exempt
def add_file(request, uuid, subfolder):
    ip = InformationPackage.objects.get(uuid=uuid)
    # template = loader.get_template('sipcreator/detail.html')
    # upload_file_form = TinyUploadFileForm()
    # repr_dir = os.path.join(ip.path,"representations")
    repname = ""
    if request.POST.has_key('rep'):
        repname = request.POST['rep']
    repsubdir = ""
    if request.POST.has_key('subdir'):
        repsubdir = request.POST['subdir']
    # context = RequestContext(request, {
    #     'uuid': ip.uuid,
    #     'StatusProcess_CHOICES': dict(StatusProcess_CHOICES),
    #     'config_path_work': config_path_work,
    #     'uploadFileForm': upload_file_form,
    #     'repr_dirs': filter(lambda x: os.path.isdir(os.path.join(repr_dir, x)), os.listdir(repr_dir)),
    #     'ip': ip,
    #     'rep': rep,
    # })
    if subfolder.startswith("_root_"):
        subfolder = subfolder.replace("_root_", ".")
    ip_work_dir = os.path.join(config_path_work, uuid)
    upload_path = os.path.join(ip_work_dir, subfolder, repname, repsubdir)
    print upload_path

    if not os.path.exists(upload_path):
        mkdir_p(upload_path)
    if request.method == 'POST':
        form = TinyUploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_aip(ip_work_dir, upload_path, request.FILES['content_file'])
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))
    if not repname and request.session.has_key('rep'):
        repname = request.session['rep']
    url = "/earkweb/sipcreator/detail/%s/%s/" % (str(ip.id), repname)
    return HttpResponseRedirect(url)
    #return HttpResponse(template.render(context))


# @login_required
# def add_file(request, uuid, subfolder):
#     if subfolder.startswith("_root_"):
#         subfolder = subfolder.replace("_root_", ".")
#     # ip_work_dir = os.path.join(config_path_work, uuid)
#     # upload_path = os.path.join(ip_work_dir, subfolder, datafolder)
#     # if not os.path.exists(upload_path):
#     #     mkdir_p(upload_path)
#     # if request.method == 'POST':
#     #     form = TinyUploadFileForm(request.POST, request.FILES)
#     #     if form.is_valid():
#     #         upload_aip(ip_work_dir, upload_path, request.FILES['content_file'])
#     #     else:
#     #         if form.errors:
#     #             for error in form.errors:
#     #                 print(str(error) + str(form.errors[error]))
#     if request.POST.has_key('rep'):
#         print "REP: %s" % request.POST['rep']
#         if not request.session.has_key('rep') or request.session['rep'] != request.POST['rep']:
#             request.session["rep"] = request.POST['rep']
#         if request.session.has_key('rep'):
#             print request.session["rep"]
#
#     ip = InformationPackage.objects.get(uuid=uuid)
#     url = '/earkweb/sipcreator/detail/' + str(ip.id)
#     return HttpResponseRedirect(url)


def upload_aip(ip_work_dir, upload_path, f):
    print "Upload file '%s' to working directory: %s" % (f, upload_path)
    if not os.path.exists(upload_path):
        mkdir_p(upload_path)
    destination_file = os.path.join(upload_path,f.name)
    with open(destination_file, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()
    if f.name.endswith(".tar"):
        async_res = extract_and_remove_package.delay(destination_file, upload_path, os.path.join(ip_work_dir, 'metadata/sip_creation.log'))
        print "Package extraction task '%s' to extract package '%s' to working directory: %s" % (async_res.id, f.name, upload_path)

@login_required
@csrf_exempt
def initialize(request, packagename):
    uuid = getUniqueID()
    sip_struct_work_dir = os.path.join(config_path_work,uuid)

    mkdir_p(os.path.join(sip_struct_work_dir, 'metadata/descriptive'))
    #mkdir_p(os.path.join(sip_struct_work_dir, 'schemas'))
    mkdir_p(os.path.join(sip_struct_work_dir, 'representations'))

    #copy_tree_content(os.path.join(root_dir, "earkresources/schemas"), os.path.join(sip_struct_work_dir, 'representations/rep-001/schemas'))

    ignore_patterns = ('*.pyc','*.git','tmp')
    shutil.copytree(os.path.join(root_dir, "earkresources/schemas"), os.path.join(sip_struct_work_dir, 'schemas'),  ignore=shutil.ignore_patterns(*ignore_patterns))

    #shutil.copyfile(os.path.join(root_dir, "earkresources/schemas/IP.xsd"), os.path.join(sip_struct_work_dir, 'schemas/IP.xsd'))
    wf = WorkflowModules.objects.get(identifier = SIPReset.__name__)
    InformationPackage.objects.create(path=os.path.join(config_path_work, uuid), uuid=uuid, statusprocess=0, packagename=packagename, last_task=wf)
    ip = InformationPackage.objects.get(uuid=uuid)
    ip_state_xml = IpState.from_parameters(state=0, locked_val=False, last_task_value=SIPReset.__name__)
    ip_state_xml.write_doc(os.path.join(config_path_work, uuid, "state.xml"))
    return HttpResponse(str(ip.id))


@login_required
def delete(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('sipcreator/deleted.html')
    if ip.uuid:
        path = os.path.join(config_path_work, ip.uuid)
        if os.path.exists(path):
            rmtree(path)
    context = RequestContext(request, {
        'uuid': ip.uuid,
    })
    ip.delete()
    return HttpResponse(template.render(context))


@login_required
def update_parent_identifier(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('sipcreator/sipcreation.html')
    context = RequestContext(request, {
        'uuid': ip.uuid,
        'StatusProcess_CHOICES': dict(StatusProcess_CHOICES),
        'config_path_work': config_path_work,
        'form': SIPCreationPackageWorkflowModuleSelectForm(),
        'ip': ip,
    })
    return HttpResponse(template.render(context))

@login_required
@csrf_exempt
def add_representation(request, pk):
    data = {"success": False}
    ip = InformationPackage.objects.get(pk=pk)
    representation = request.POST['representation']
    try:
        if re.match("[A-Za-z0-9-_]{4,200}", representation, flags=0):
            repr_dir = os.path.join(ip.path,"representations", representation)
            if not os.path.exists(repr_dir):
                mkdir_p(repr_dir)
                mkdir_p(os.path.join(repr_dir, 'metadata'))
                mkdir_p(os.path.join(repr_dir, 'schemas'))
                mkdir_p(os.path.join(repr_dir, 'data'))
                mkdir_p(os.path.join(repr_dir, 'documentation'))
                print representation
                request.session['rep'] = representation
                data = {"success": True, "representation": representation}
            else:
                data = {"success": False, "message": "Representation already exists!"}
        else:
            data = {"success": False, "message": "Invalid representation directory name (alphanumerical with minimum length 4 and maximum length 200)!"}
    except:
        tb = traceback.format_exc()
    return JsonResponse(data)

# Methods for external (non DJANGO UI based) invocation of SIPCreator

@login_required
@csrf_exempt
def sip_uuid(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    return HttpResponse(ip.uuid)

@login_required
@csrf_exempt
def ins_file(request, uuid, subfolder):
    ip = InformationPackage.objects.get(uuid=uuid)

    repname = ""
    if request.POST.has_key('rep'):
        repname = request.POST['rep']
        print "repname=%s" % repname

    repsubdir = ""
    if request.POST.has_key('subdir'):
        repsubdir = request.POST['subdir']
        print "repsubdir=%s" % repsubdir

    if subfolder.startswith("_root_"):
        subfolder = subfolder.replace("_root_", ".")
        print "subfolder=%s" % subfolder

    ip_work_dir = os.path.join(config_path_work, uuid)
    upload_path = os.path.join(ip_work_dir, subfolder, repname, repsubdir)
    print "upload_path=%s" % upload_path

    if not os.path.exists(upload_path):
        mkdir_p(upload_path)

    if request.method == 'POST':
        form = TinyUploadFileForm(request.POST, request.FILES)
        print request.FILES
        if form.is_valid():
            print "valid form"
            upload_aip(ip_work_dir, upload_path, request.FILES['content_file'])
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))

    return HttpResponse("success")

@login_required
@csrf_exempt
def finalize(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    return HttpResponse("success")


class SipCreationBatchView(ListView):
    """
    Processing status
    """
    model = WorkflowModules
    template_name = 'sipcreator/batch.html'
    context_object_name = 'sips'

    queryset=InformationPackage.objects.extra(where=["last_task_id='%s'" % SIPReset.__name__]).order_by('last_change')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SipCreationBatchView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SipCreationBatchView, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        context['flower_url'] = "http://%s:%s%s" % (flower_server, flower_port, flower_path)
        return context


@login_required
@csrf_exempt
def poll_state(request):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                if task.state == "SUCCESS":
                    aggr_log = '\n'.join(task.result.log)
                    aggr_err = '\n'.join(task.result.err)
                    data = {"success": True, "result": task.result.success, "state": task.state, "log": aggr_log, "err": aggr_err}
                elif task.state == "PROGRESS":
                    data = {"success": True, "result": task.state, "state": task.state, "info": task.info}
            else:
                data = {"success": False, "errmsg": "No task_id in the request"}
        else:
            data = {"success": False, "errmsg": "Not ajax"}
    except Exception, err:
        data = {"success": False, "errmsg": err.message}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)


@login_required
@csrf_exempt
def submit_sipcreation_batch(request, uuid):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            try:
                ip = InformationPackage.objects.get(uuid=uuid)
                job = run_sipcreation_batch.delay(uuid=uuid, packagename=ip.packagename, path=ip.path)
                data = {"success": True, "id": job.id, "uuid": uuid}
            except Exception, err:
                tb = traceback.format_exc()
                logging.error(str(tb))
                data = {"success": False, "errmsg": "Error", "errdetail": str(tb)}
        else:
            data = {"success": False, "errmsg": "not ajax"}
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = {"success": False, "errmsg": err.message, "errdetail": str(tb)}
        return JsonResponse(data)
    return JsonResponse(data)