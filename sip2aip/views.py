import os
import traceback
from django.template import loader
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.contrib.auth.decorators import login_required
import requests
from requests.packages.urllib3.exceptions import ConnectionError
from earkcore.models import StatusProcess_CHOICES
from earkcore.models import InformationPackage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
from earkcore.utils.randomutils import getUniqueID
from earkcore.utils.serviceutils import service_available
from earkcore.utils.stringutils import whitespace_separated_text_to_dict
from sandbox.sipgenerator.sipgenerator import SIPGenerator
from sip2aip.forms import UploadSIPDeliveryForm
from workers import tasks
from django.http import JsonResponse
from sip2aip import forms
from workers.ip_state import IpState
from workers.taskconfig import TaskConfig
from workers.tasks import SIPtoAIPReset, AIPIndexing, AIPStore, run_package_ingest, IPClose, DIPStore, IPDelete
from workflow.models import WorkflowModules
from config.configuration import config_path_work
from config.configuration import config_path_reception
from earkcore.utils.fileutils import mkdir_p
from django.core.urlresolvers import reverse
from workers.tasks import LilyHDFSUpload
from workers.tasks import SolrUpdateCurrentMetadata
from config.configuration import storage_solr_server_ip
from config.configuration import django_service_port
from config.configuration import django_service_ip
from config.configuration import storage_solr_core
from config.configuration import storage_solr_port
from workers.tasks import reception_dir_status
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig
from config.configuration import access_solr_port, access_solr_server_ip, access_solr_core

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

class InformationPackageTable(tables.Table):

    from django_tables2.utils import A
    area = "sip2aip"

    identifier = tables.Column(verbose_name='Identifier' )
    last_task = tables.Column(verbose_name='Last task')
    statusprocess = tables.Column(verbose_name='Outcome' )
    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name= 'Last change')
    uuid = tables.LinkColumn('%s:working_area' % area, kwargs={'section': area, 'uuid': A('uuid')}, verbose_name= 'Process ID')
    packagename = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name= 'Package name')

    class Meta:
        model = InformationPackage
        fields = ('packagename', 'uuid', 'identifier', 'last_change', 'last_task', 'statusprocess')
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
    area = "sip2aip"
    areacode = "2"
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


class IndexingStatusTable(tables.Table):

    from django_tables2.utils import A

    identifier = tables.LinkColumn('earkcore:ipview', args={A('identifier')}, verbose_name= 'Identifier')

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name= 'Last change')
    last_task = tables.Column(verbose_name='Last task' )
    #packagename = tables.LinkColumn('sip2aip:ip_detail', kwargs={'pk': A('pk')}, verbose_name= 'Package name')
    num_indexed_docs_storage = tables.Column(verbose_name= 'Number of indexed documents' )


    class Meta:
        model = InformationPackage
        fields = ('identifier', 'last_change', 'last_task', 'num_indexed_docs_storage')
        attrs = {'class': 'paleblue table table-striped table-bordered table-condensed' }
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_num_indexed_docs_storage(value):
        return mark_safe('<b>%s</b>' % value)

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


def indexingstatus(request):
    """
    Indexing Status Table view
    """
    local_solr = 'http://%s:%s/solr/%s/admin/ping' % (storage_solr_server_ip, storage_solr_port, storage_solr_core)
    if not service_available(local_solr):
        return render(request, 'earkweb/error.html', {'header': 'SolR server unavailable', 'message': "Required service is not available at: %s" % local_solr})
    list_tasks = [
        "last_task_id='%s'" % AIPIndexing.__name__,
        "last_task_id='%s'" % SolrUpdateCurrentMetadata.__name__,
        "last_task_id='%s'" % AIPStore.__name__,
        "last_task_id='%s'" % DIPStore.__name__,
        "last_task_id='%s'" % IPClose.__name__,
        "last_task_id='%s'" % IPDelete.__name__,
    ]
    task_cond = " or ".join(list_tasks)
    # where=["(%s)" % task_cond]
    queryset=InformationPackage.objects.extra(where=["storage_loc != ''"]).order_by('-last_change')
    table = IndexingStatusTable(queryset)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    return render(request, 'sip2aip/indexing_status.html', {'informationpackage': table})


class StoredIPTable(tables.Table):

    from django_tables2.utils import A

    identifier = tables.LinkColumn('earkcore:ipview', args={A('identifier')}, verbose_name= 'Identifier')

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name= 'Last change')
    # last_task = tables.Column(verbose_name='Last task' )
    # packagename = tables.LinkColumn('sip2aip:ip_detail', kwargs={'pk': A('pk')}, verbose_name= 'Package name')
    # num_indexed_docs_storage = tables.Column(verbose_name= 'Number of indexed documents' )
    storage_loc = tables.Column(verbose_name='Storage Location')
    num_indexed_docs_storage = tables.Column(verbose_name= 'Number of indexed documents' )

    class Meta:
        model = InformationPackage
        fields = ('identifier', 'last_change', 'storage_loc', 'num_indexed_docs_storage')
        attrs = {'class': 'paleblue table table-striped table-bordered table-condensed' }
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


def hdfs_batch_upload(request):
    """
    Indexing Status Table view
    """
    lily_solr = 'http://%s:%s/solr/%s/admin/ping' % (access_solr_server_ip, access_solr_port, access_solr_core)
    if not service_available(lily_solr):
        return render(request, 'earkweb/error.html', {'header': 'SolR server unavailable', 'message': "Required service is not available at: %s" % lily_solr})
    list_tasks = [
        "last_task_id='%s'" % AIPIndexing.__name__,
        "last_task_id='%s'" % SolrUpdateCurrentMetadata.__name__,
        "last_task_id='%s'" % AIPStore.__name__,
        "last_task_id='%s'" % DIPStore.__name__,
        "last_task_id='%s'" % IPClose.__name__,
        "last_task_id='%s'" % IPDelete.__name__,
    ]
    task_cond = " or ".join(list_tasks)
    # where=["(%s)" % task_cond]
    queryset = InformationPackage.objects.extra(where=["storage_loc != ''"]).order_by('-last_change')
    table = StoredIPTable(queryset)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    return render(request, 'sip2aip/hdfs_batch_upload.html', {'storedip': table})


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


@login_required
def aipsearch_package(request):
    template = loader.get_template('sip2aip/aipsearch_package.html')
    context = RequestContext(request, {
        'local_solr_server_ip': storage_solr_server_ip,
        'django_service_ip': django_service_ip,
        'django_service_port': django_service_port,
        'local_solr_port': storage_solr_port,
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
    from config.configuration import max_submissions_web_client
    from config.configuration import flower_server
    from config.configuration import flower_port
    from config.configuration import flower_path
    context = RequestContext(request, {
        'config_path_reception': config_path_reception,
        'max_submissions_web_client': max_submissions_web_client,
        'flower_url': "http://%s:%s%s" % (flower_server, flower_port, flower_path),
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
    predef_id_mapping = {}
    if 'predef_id_mapping' in request.POST.keys():
        predef_id_mapping = whitespace_separated_text_to_dict(request.POST['predef_id_mapping'])
    print "PREDEF_MAPPING: %s" % predef_id_mapping
    try:
        if request.is_ajax():
            try:
                job = run_package_ingest.delay(package_file=package_file, predef_id_mapping=predef_id_mapping)
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
