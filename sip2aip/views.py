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
from sandbox.sipgenerator.sipgenerator import SIPGenerator
from sip2aip.forms import UploadSIPDeliveryForm
from workers import tasks
from django.http import JsonResponse
from sip2aip import forms
from workers.ip_state import IpState
from workers.taskconfig import TaskConfig
from workers.tasks import SIPtoAIPReset, AIPIndexing, AIPStore, run_package_ingest
from workflow.models import WorkflowModules
from config.configuration import config_path_work
from config.configuration import config_path_reception
from earkcore.utils.fileutils import mkdir_p
from django.core.urlresolvers import reverse
from workers.tasks import LilyHDFSUpload
from config.configuration import local_solr_server_ip
from config.configuration import django_service_port
from config.configuration import django_service_ip
from config.configuration import local_solr_port
from workers.tasks import reception_dir_status


import logging
logger = logging.getLogger(__name__)

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
    return render_to_response('sip2aip/iptable.html', locals(), context_instance=context)


@login_required
def index(request):
    template = loader.get_template('sip2aip/index.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))


class IndexingStatusList(ListView):
    """
    Processing status
    """
    model = InformationPackage
    template_name = 'sip2aip/indexing_status.html'
    context_object_name = 'ips'

    list_tasks = [
        "last_task_id='%s'" % AIPIndexing.__name__,
        "last_task_id='%s'" % LilyHDFSUpload.__name__,
        "last_task_id='%s'" % AIPStore.__name__,
    ]
    task_cond = " or ".join(list_tasks)

    queryset=InformationPackage.objects.extra(where=["identifier!='' and (%s)" % task_cond]).order_by('last_change')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IndexingStatusList, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexingStatusList, self).get_context_data(**kwargs)
        return context


@login_required
def upload_sip(request):
    template = loader.get_template('sip2aip/upload_sip.html')
    form = UploadSIPDeliveryForm()
    context = RequestContext(request, {
        'form': form
    })
    return HttpResponse(template.render(context))


@login_required
def upload_sip_delivery(request):
    uuid = getUniqueID()
    upload_directory = os.path.join(config_path_work, uuid)
    print "upload directory: %s" % upload_directory
    if request.method == 'POST':
        form = UploadSIPDeliveryForm(request.POST, request.FILES)
        if form.is_valid():
            sip_tar_package_file = request.FILES['sip_tar_package']
            packagename, _ = os.path.splitext(os.path.basename(sip_tar_package_file.name))
            sip_delivery_xml = None
            deliveryname = None
            if 'sip_delivery_xml' in request.FILES:
                sip_delivery_xml = request.FILES['sip_delivery_xml']
                deliveryname, _ = os.path.splitext(os.path.basename(sip_delivery_xml.name))
            form = UploadSIPDeliveryForm()
            if deliveryname and packagename != deliveryname:
                context = RequestContext(request, {
                    'error': 'File name without extension must be equal, i.e. <packagename>.tar and <packagename>.xml',
                    'form': form
                })
                template = loader.get_template('sip2aip/upload_sip.html')
                return HttpResponse(template.render(context))
            else:
                upload_file(upload_directory, sip_tar_package_file)
                if sip_delivery_xml:
                    upload_file(upload_directory, sip_delivery_xml)
                else:
                    sipgen = SIPGenerator(upload_directory)
                    delivery_mets_file = os.path.join(upload_directory, packagename + '.xml')
                    _, file_extension = os.path.splitext(sip_tar_package_file.name)
                    dest_package_file = os.path.join(upload_directory, packagename + file_extension)
                    sipgen.createDeliveryMets(dest_package_file, delivery_mets_file)
                    logger.info( "Delivery METS stored: %s" % delivery_mets_file )
                path = upload_directory
                initial_last_task = WorkflowModules.objects.get(identifier=SIPtoAIPReset.__name__)
                ip = InformationPackage.objects.create(uuid=uuid, packagename=packagename, path=path, statusprocess=0, last_task=initial_last_task)
                ip.save()
                IpState.from_parameters(0, "False", SIPtoAIPReset.__name__).write_doc(os.path.join(upload_directory, 'state.xml'))
                url = reverse('sip2aip:ip_detail', args=(ip.id,))
                return HttpResponseRedirect(url)
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))
            return HttpResponseServerError("Upload error")


def upload_file(upload_path, f):
    print "Upload file '%s' to working directory: %s" % (f.name, upload_path)
    if not os.path.exists(upload_path):
        mkdir_p(upload_path)
    destination_file = os.path.join(upload_path, f.name)
    with open(destination_file, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()


class InformationPackageList(ListView):
    """
    Information Package List View
    """
    status_lower_limit = 100
    status_upper_limit = 10000
    filter_divisor = 20 # used with modulo operator to filter status values

    model = InformationPackage
    template_name = 'sip2aip/reception.html'
    context_object_name = 'ips'

    sql_query = """
    select ip.id as id, ip.path as path, ip.statusprocess as statusprocess, ip.uuid as uuid, ip.packagename as packagename, ip.identifier as identifier
    from workflow_workflowmodules as wf
    inner join earkcore_informationpackage as ip
    on wf.identifier=ip.last_task_id
    where wf.tstage & 2
    order by ip.last_change desc;
    """
    queryset = InformationPackage.objects.raw(sql_query)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InformationPackageList, self).dispatch(*args, **kwargs)

    def get_success_status_set(self, status_model, filter_func):
        for tuple in status_model:
            if (self.status_lower_limit <= tuple[0] < self.status_upper_limit) and filter_func(tuple[0]):
                yield tuple[0], tuple[1]

    def get_context_data(self, **kwargs):
        context = super(InformationPackageList, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        success_status_set = self.get_success_status_set(StatusProcess_CHOICES, lambda arg: arg % self.filter_divisor == 0)
        error_status_set = self.get_success_status_set(StatusProcess_CHOICES, lambda arg: arg % self.filter_divisor != 0)
        context['success_status_set'] = success_status_set
        context['error_status_set'] = error_status_set
        context['config_path_work'] = config_path_work
        context['working_directory_available'] = os.path.exists(os.path.join(config_path_work))
        return context

@login_required
def aipsearch_package(request):
    template = loader.get_template('sip2aip/aipsearch_package.html')
    context = RequestContext(request, {
        'local_solr_server_ip': local_solr_server_ip,
        'django_service_ip': django_service_ip,
        'django_service_port': django_service_port,
        'local_solr_port': local_solr_port,
    })
    return HttpResponse(template.render(context))


class HelpProcessingStatus(ListView):
    """
    Processing status
    """
    model = WorkflowModules
    template_name = 'sip2aip/help_processing_status.html'
    context_object_name = 'wfms'

    queryset=WorkflowModules.objects.extra(where=["ttype & %d" % 2]).order_by('ordval')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HelpProcessingStatus, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HelpProcessingStatus, self).get_context_data(**kwargs)
        return context


class InformationPackageDetail(DetailView):
    """
    Information Package Detail View
    """
    model = InformationPackage
    context_object_name = 'ip'
    template_name = 'sip2aip/detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InformationPackageDetail, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InformationPackageDetail, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        context['form'] = forms.SIPtoAIPWorkflowModuleSelectForm()
        context['config_path_work'] = config_path_work
        return context

class InformationPackageDetail2(DetailView):
    """
    Information Package Detail View
    """
    model = InformationPackage
    context_object_name = 'ip'
    template_name = 'sip2aip/detail2.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InformationPackageDetail2, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InformationPackageDetail2, self).get_context_data(**kwargs)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        context['form'] = forms.SIPtoAIPWorkflowModuleSelectForm2()
        context['config_path_work'] = config_path_work
        return context


@login_required
def progress(request):
    context = RequestContext(request, {
        'form': forms.PackageWorkflowModuleSelectForm()
    })
    return render_to_response('sip2aip/progress.html', locals(), context_instance=context)


@login_required
@csrf_exempt
def apply_workflow(request):
    print request
    data = {"success": False, "errmsg": "Unknown error"}
    print data
    try:
        print "Workflow execution"
        # selected_ip = request.POST['selected_ip']
        # print "selected_ip: " + request.POST['selected_ip']
        # selected_action = request.POST['selected_action']
        # print "selected_action: " + request.POST['selected_action']
        # if not (selected_ip and selected_action):
        #     return JsonResponse({"success": False, "errmsg": "Missing input parameter!"})
        # wfm = WorkflowModules.objects.get(pk=selected_action)
        # tc = TaskConfig(wfm.expected_status,  wfm.success_status, wfm.error_status)
        # if request.is_ajax():
        #     taskClass = getattr(tasks, wfm.identifier)
        #     print "Executing task: %s" % wfm.identifier
        #     job = taskClass().apply_async((selected_ip, tc,), queue='default')
        #     print "Task identifier: %s" % job.id
        #     data = {"success": True, "id": job.id}
        # else:
        #     data = {"success": False, "errmsg": "not ajax"}
        data = {"success": True, "id": "xyz", "myprop": "val"}
    except:
        tb = traceback.format_exc()
        logger.error(str(tb))
        data = {"success": False, "errmsg": "an error occurred!"}
        return JsonResponse(data)
    return JsonResponse(data)


@login_required
@csrf_exempt
def apply_task(request):
    try:
        data = {"success": False, "errmsg": "Unknown error"}
        selected_ip = request.POST['selected_ip']
        print "selected_ip: " + request.POST['selected_ip']
        selected_action = request.POST['selected_action']
        print "selected_action: " + request.POST['selected_action']
        if not (selected_ip and selected_action):
            return JsonResponse({"success": False, "errmsg": "Missing input parameter!"})
        wfm = WorkflowModules.objects.get(pk=selected_action)
        tc = TaskConfig(wfm.expected_status,  wfm.success_status, wfm.error_status)
        if request.is_ajax():
            taskClass = getattr(tasks, wfm.identifier)
            print "Executing task: %s" % wfm.identifier
            job = taskClass().apply_async((selected_ip, tc,), queue='default')
            print "Task identifier: %s" % job.id
            data = {"success": True, "id": job.id}
        else:
            data = {"success": False, "errmsg": "not ajax"}
    except:
        tb = traceback.format_exc()
        logger.error(str(tb))
        data = {"success": False, "errmsg": "an error occurred!"}
        return JsonResponse(data)
    return JsonResponse(data)


@login_required
def batch(request):
    template = loader.get_template('sip2aip/batch.html')
    from config.configuration import config_path_reception
    context = RequestContext(request, {
        'config_path_reception': config_path_reception
    })
    return HttpResponse(template.render(context))


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
        logger.error(str(tb))
    return JsonResponse(data)


@login_required
@csrf_exempt
def submit_package_ingest(request, package_file):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            try:
                job = run_package_ingest.delay(package_file=package_file)
                data = {"success": True, "id": job.id, "packagefile": package_file}
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