import functools
import json
import logging
import os
import tarfile
import traceback
import urllib
from threading import Thread

import requests
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.template import RequestContext, loader
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from lxml import etree

from config.configuration import config_path_work, config_path_storage
from earkcore.models import InformationPackage
from earkcore.storage.pairtreestorage import PairtreeStorage
from earkcore.utils.fileutils import mkdir_p
from earkcore.utils.randomutils import getUniqueID
from earkcore.utils.stringutils import lstrip_substring
from earkcore.utils.stringutils import safe_path_string
from forms import SearchForm, UploadFileForm
from models import AIP, DIP, Inclusion
from query import get_query_string
from sip2aip.forms import AIPtoDIPWorkflowModuleSelectForm
from workers.default_task_context import DefaultTaskContext
from workflow.models import WorkflowModules

logger = logging.getLogger(__name__)
from django.shortcuts import render_to_response
from earkcore.models import StatusProcess_CHOICES
from workers.tasks import AIPtoDIPReset

from earkcore.xml.xmlvalidation import XmlValidation
from config.configuration import server_hdfs_aip_query

from config.configuration import server_repo_record_content_query
import time
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig

def initialize_dip(dip_creation_process_name):
    dip = DIP.objects.create(name=dip_creation_process_name)
    uuid = getUniqueID()
    wf = WorkflowModules.objects.get(identifier = AIPtoDIPReset.__name__)
    InformationPackage.objects.create(path=os.path.join(config_path_work, uuid), uuid=uuid, statusprocess=0, packagename=dip_creation_process_name, last_task=wf)
    work_dir = "%s/%s" % (config_path_work, uuid)
    task_context = DefaultTaskContext(uuid, work_dir, 'AIPtoDIPReset', None, {'packagename' : dip_creation_process_name }, None)
    AIPtoDIPReset().apply((task_context,), queue='default')


@login_required
def index(request, procname):
    if DIP.objects.count() == 0:
        generated_dip_packagename = 'DIP-%s' % time.strftime("%Y%m%d-%H%M%S")
        initialize_dip(generated_dip_packagename)
    template = loader.get_template('search/index.html')
    form = SearchForm()
    from config.configuration import django_service_ip
    from config.configuration import django_service_port
    context = RequestContext(request, {
        'django_service_ip': django_service_ip,
        'django_service_port': django_service_port,
        'form': form,
        'dips': DIP.objects.all(),
        'procname': procname
    })
    return HttpResponse(template.render(context))

@login_required
def packsel(request):

    status_lower_limit = 0
    status_upper_limit = 100
    filter_divisor = 2 # used with modulo operator to filter status values

    dips = DIP.objects.all()
    template = loader.get_template('search/packsel.html')

    def get_success_status_set(status_model, filter_func):
        for tuple in status_model:
            if (status_lower_limit < tuple[0] < status_upper_limit) and filter_func(tuple[0]):
                yield tuple[0], tuple[1]

    success_status_set = get_success_status_set(StatusProcess_CHOICES, lambda arg: arg % filter_divisor == 0)
    error_status_set = get_success_status_set(StatusProcess_CHOICES, lambda arg: arg % filter_divisor != 0)

    context = RequestContext(request, {
        'package_list': dips,
        'success_status_set': success_status_set,
        'error_status_set': error_status_set,
    })
    return HttpResponse(template.render(context))


class InformationPackageTable(tables.Table):

    from django_tables2.utils import A
    area = "aip2dip"

    packagename = tables.LinkColumn('search:dip', args={A('packagename')}, verbose_name= 'Package name')
    uuid = tables.LinkColumn('search:working_area', kwargs={'section': area, 'uuid': A('uuid')}, verbose_name= 'Process ID')
    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name= 'Last change')
    last_task = tables.Column(verbose_name='Last task')
    statusprocess = tables.Column(verbose_name='Outcome' )

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
    area = "aip2dip"
    areacode = "4"
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
        return render(request, 'search/packsel.html', {'informationpackage': table})


@login_required
@csrf_exempt
def selectedaipstable(request):
    dip_name = request.POST['dip_name']
    print "Update DIP table with the new list of AIPs: %s" % dip_name
    dip = DIP.objects.get(name=dip_name)
    context = RequestContext(request, {
        'dip': dip,
    })
    return render_to_response('search/selectedaipstable.html', locals(), context_instance=context)


@login_required
@csrf_exempt
def aipselectiondropdown(request):
    filterword = request.POST['filterword'] if 'filterword' in request.POST.keys() else ""
    aips = InformationPackage.objects.extra(where=["identifier != '' AND identifier like '%%{0}%%'".format(filterword)]).order_by('-last_change')[:10]
    print "NUMBER: %d" % len(aips)
    print filterword
    context = RequestContext(request, {
        'aips': aips,
    })
    return render_to_response('search/aipselectiondropdown.html', locals(), context_instance=context)


class HelpProcessingStatus(ListView):
    """
    Processing status
    """
    model = WorkflowModules
    template_name = 'search/help_processing_status.html'
    context_object_name = 'wfms'

    queryset=WorkflowModules.objects.extra(where=["ttype & %d" % 4]).order_by('ordval')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HelpProcessingStatus, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HelpProcessingStatus, self).get_context_data(**kwargs)
        return context


@login_required
def start(request):
    dips = DIP.objects.all()
    template = loader.get_template('search/start.html')
    context = RequestContext(request, {
        'package_list': dips
    })
    return HttpResponse(template.render(context))

@login_required
def aip(request, dip_name, identifier):
    dip = DIP.objects.get(name=dip_name)
    aip = dip.aips.get(identifier=identifier)
    template = loader.get_template('search/aip.html')
    context = RequestContext(request, {'dip': dip, 'aip': aip})
    return HttpResponse(template.render(context))


@login_required
def localrepo(request):
    template = loader.get_template('search/localrepo.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
def demosearch(request):
    template = loader.get_template('search/demosearch.html')
    context = RequestContext(request, {
        
    })
    return HttpResponse(template.render(context))

@login_required
def demosearch_govdocs(request):
    template = loader.get_template('search/demosearch_govdocs.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
def demosearch_news(request):
    template = loader.get_template('search/demosearch_news.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
def demosearch_package(request):
    template = loader.get_template('search/demosearch_package.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
@csrf_exempt
def remproc(request):
    try:
        dip_name = lstrip_substring(request.POST['remproc'], "remproc")
        dip = DIP.objects.get(name=dip_name)
        dip.delete()

        ip = InformationPackage.objects.get(packagename=dip_name)
        if ip:
            ip.delete()

        incls = Inclusion.objects.filter(dip=dip)
        for incl in incls:
            incl.delete()

        resultDict = {'success': True}
        docsjson = json.dumps(resultDict, indent=4)
        return HttpResponse(docsjson)
    except Exception:
        error = {'success': False, "error": "Error processing request"}
        logger.error(traceback.format_exc())
        return HttpResponseServerError(json.dumps(error))


@login_required
@csrf_exempt
def remaip(request):
    try:
        remaip = lstrip_substring(request.POST['remaip'], "remaip").split("~")
        if len(remaip) == 2:
            dip_name = remaip[0]
            dip = DIP.objects.get(name=dip_name)
            aip_identifier = remaip[1]
            aip = AIP.objects.get(identifier=aip_identifier)
            incl = Inclusion.objects.get(aip=aip, dip=dip)
            incl.delete()
            resultDict = {'success': True, "dip_name": dip.safe_path_string(), "aip_identifier": aip.safe_string()}
        else:
            resultDict = {'success': False, "error": "Invalid request parameters"}
        docsjson = json.dumps(resultDict, indent=4)
        return HttpResponse(docsjson)
    except Exception:
        error = {'success': False, "error": "Error processing request", "detail": traceback.format_exc()}
        logger.error(traceback.format_exc())
        return HttpResponseServerError(json.dumps(error))

@login_required
def search_form(request):
    if request.POST:
        form = SearchForm(request.POST)
        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            content_type = form.cleaned_data['content_type']
            package = form.cleaned_data['package'].replace(":", "\\:")
            representation_data_only = form.cleaned_data['representation_data_only']
            logger.debug("representation_data_only: %s" % representation_data_only)
            start = 0
            rows = 100
            query_string = get_query_string(keyword, content_type, package, representation_data_only, start, rows)
            logger.debug("Query string: %s" % query_string)
            dip_name = request.POST["dip"]
            dip = DIP.objects.get(name=dip_name)
            selectedObjects = dip.aips.all()
            try: 
                response = requests.get(query_string)
                responseJson = response.json()
                numFound = responseJson["response"]["numFound"]
                docs = responseJson["response"]["docs"]  
                documents = list()
                for doc in docs:
                    responseObj = dict()
                    responseObj['title'] = doc["path"]
                    if doc.has_key('lily_id'):
                        responseObj['lily_id'] = urllib.quote_plus(doc["lily.id"])
                    else:
                        responseObj['lily_id'] = doc["path"]
                    if doc.has_key('contentType'):
                        responseObj['contentType'] = doc["contentType"]
                    else:
                        responseObj['contentType'] = doc["content_type"]

                    if doc.has_key('size'):
                        responseObj['size'] = doc["size"]
                    else:
                        responseObj['size'] = doc["stream_size"]
                    # get package property from path
                    responseObj['is_selected_pack'] = False
                    packageSep = doc["path"].find("/")
                    if packageSep != -1:
                        responseObj['pack'] = doc["path"][0:packageSep]
                        if selectedObjects.filter(identifier=responseObj['pack']).exists():
                            responseObj['is_selected_pack'] = True
                    else:
                        responseObj['pack'] = "Unknown"
                    if responseObj['lily_id'] != "":
                        documents.append(responseObj)
                resultDict = {'numFound':numFound, 'start': start, 'rows': rows, 'documents': documents}
                docsjson = json.dumps(resultDict, indent=4)

            except Exception:
                error = {"error":"Error processing request"}
                logger.error(traceback.format_exc())
                return HttpResponseServerError(json.dumps(error))
            if request.is_ajax():
                return HttpResponse(docsjson)
            else:
                pass
        else:
            if request.is_ajax():
                errors_dict = {}
                if form.errors:
                    for error in form.errors:
                        e = form.errors[error]
                        errors_dict[error] = unicode(e)
                return HttpResponseBadRequest(json.dumps(errors_dict))
            else:
                pass
    else:
        form = SearchForm()
    context = {'form':form}
    return render(request, 'search/index.html', context)

@login_required
@csrf_exempt
def toggle_select_package(request):
    if request.method == "POST":
        print "identifier:", request.POST["identifier"]
        print "action:", request.POST["action"]
        print "dip:", request.POST["dip"]

        if request.POST.__contains__("identifier") and request.POST.__contains__("dip"):
            identifier = request.POST["identifier"]
            dip_name = request.POST["dip"]
            dip = DIP.objects.get(name=dip_name)
            ip = InformationPackage.objects.get(identifier=identifier)
            if not ip:
                return HttpResponse("{ \"success\": \"false\",  \"message\": \"missing package for identifier %s \" }" % identifier)
            if request.POST["action"] == "add":
                if AIP.objects.filter(identifier=identifier).count() == 0:
                    aip = AIP.objects.create(identifier=identifier, cleanid="", source=ip.storage_loc, date_selected=timezone.now())
                    Inclusion(aip=aip, dip=dip).save()
                    print "Added new package %s" % identifier
                elif dip.aips.filter(identifier=identifier).count() == 0:
                    aip = AIP.objects.filter(identifier=identifier)[0]
                    Inclusion(aip=aip, dip=dip).save()
                    print "Added existing package %s" % identifier
                else:
                    print "Package %s already added" % identifier
            elif request.POST["action"] == "remove":
                aip = AIP.objects.filter(identifier=identifier)[0]
                Inclusion.objects.filter(aip=aip, dip=dip).delete()
                logger.debug("Removed package %s" % identifier)
            else:
                return HttpResponse("{ \"success\": \"false\",  \"message\": \"action not supported\" }")
        else:
            return HttpResponse("{ \"success\": \"false\",  \"message\": \"request method not supported\" }")
        return HttpResponse("{ \"success\": \"true\" }")
    else:
        return render(request, 'search/index.html')


@login_required
def get_file_content(request, lily_id):
    logger.debug("Get content for lily_id %s" % lily_id)
    if request.is_ajax():
        query_url =  server_repo_record_content_query.format(lily_id)
        logger.debug("Get file content query: %s" % query_url)
        r = requests.get(query_url, stream=True)
        logger.debug("Get file content query status code: %d" % r.status_code)
        logger.debug("Get file content query content-type: %s" % r.headers['content-type'])
        contentType = r.headers['content-type']
        response_content = r.text
        response_content_utf8 = response_content.encode("utf-8")
        if contentType == 'application/xml': 
            try:
                tree = etree.fromstring(response_content_utf8)
                # List containing names you want to keep
                inputID = ['agent', 'dmdSec', 'fileSec']
                
                for node in tree.findall('.//data'):
                    # Remove node if the name attribute value is not in inputID
                    if not node.attrib.get('name') in inputID:
                        tree.getroot().remove(node)
                print etree.tostring(tree)
            except Exception:                
                logger.error(traceback.format_exc())
        return HttpResponse(r.text)
    else:
        pass


@login_required
def create_dip(request):
    if request.method == "POST":
        dip_creation_process_name = request.POST['dip_creation_process_name']
        if DIP.objects.filter(name = dip_creation_process_name).count() > 0:
            template = loader.get_template('search/start.html')
            context = RequestContext(request, {
                'procname': dip_creation_process_name,
                'error': "Process already exists!"
            })
            return HttpResponse(template.render(context))
        else:
            initialize_dip(dip_creation_process_name)
            url = reverse('search:dip', args=(dip_creation_process_name,))
            return HttpResponseRedirect(url)
    else:
        pass

@login_required
def acquire_aips(request, dip_name):
    if request.method == "POST":
        dip = DIP.objects.get(name=dip_name)
        aips = dip.aips.filter(inclusion__stored=False)
        thread = Thread(target=functools.partial(copy_to_local, aips), args=(), kwargs={})
        thread.start()
        return HttpResponseRedirect(reverse('search:packsel'))
    else:
        pass

@login_required
def attach_aip(request, dip_name):
    if request.method == 'POST':
        dip = DIP.objects.get(name=dip_name)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_aip(dip, request.FILES['local_aip'])
            #return HttpResponseRedirect(reverse('search:packsel'))
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))
            #return HttpResponseRedirect(reverse('search:packsel'))

        url = reverse('search:dip', args={dip_name})
        return HttpResponseRedirect(url)
    else:
        pass

def upload_aip(dip, f):
    dip_name_dir = safe_path_string(dip.name)
    dip_name_work_dir = os.path.join(config_path_work,dip_name_dir)
    print "Upload file '%s' to working directory: %s" % (f, dip_name_work_dir)
    if not os.path.exists(dip_name_work_dir):
        mkdir_p(dip_name_work_dir)
    destination_file = os.path.join(dip_name_work_dir,f.name)
    with open(destination_file, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    identifier = f.name.rpartition('.')[0]

    aip = AIP.objects.filter(identifier=identifier)

    incl = Inclusion.objects.filter(aip=aip, dip=dip)

    if aip.count() == 0 or incl.count() == 0:
        aip = AIP.objects.create(identifier=identifier, cleanid="unused", source=destination_file, date_selected=timezone.now())
        Inclusion(aip=aip, dip=dip, stored=True).save()
    else:
        print "Object not added, already exists"

def copy_to_local(aips):
    for aip in aips:
        filename = aip.identifier + '.tar'
        logger.info('copying AIP %s from HDFS' % aip)
        r = requests.get(server_hdfs_aip_query.format(filename))
        with open('working_area/' + filename, 'w') as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
        extractTar(filename)

def extractTar(filename):
    with tarfile.open('working_area/' + filename) as tar:
        tar.extractall('working_area/')


@login_required
def aipselection(request, name):
    dip = DIP.objects.get(name=name)
    ip = InformationPackage.objects.get(packagename=name)
    template = loader.get_template('search/aipselection.html')
    form = AIPtoDIPWorkflowModuleSelectForm()
    stat_proc_choices = dict(StatusProcess_CHOICES),
    context = RequestContext(request, {'dip': dip, 'ip': ip, 'uploadFileForm': UploadFileForm(), 'form': form,  "StatusProcess_CHOICES": stat_proc_choices[0], "config_path_work": config_path_work})
    return HttpResponse(template.render(context))


@login_required
def dip(request, name):
    dip = DIP.objects.get(name=name)
    ip = InformationPackage.objects.get(packagename=name)
    template = loader.get_template('search/dip.html')
    form = AIPtoDIPWorkflowModuleSelectForm()
    stat_proc_choices = dict(StatusProcess_CHOICES),
    context = RequestContext(request, {'dip': dip, 'ip': ip, 'uploadFileForm': UploadFileForm(), 'form': form,  "StatusProcess_CHOICES": stat_proc_choices[0], "config_path_work": config_path_work})
    return HttpResponse(template.render(context))
    #return render_to_response('search/dip.html', {'dip': dip, 'uploadFileForm': UploadFileForm()})

@login_required
@csrf_exempt
def dip_detail_table(request):
    pkg_id = request.POST['pkg_id']

    ip = InformationPackage.objects.get(pk=pkg_id)
    dip = DIP.objects.get(name=ip.packagename)

    context = RequestContext(request, {
        "ip": ip,
        "dip": dip,
        "StatusProcess_CHOICES": dict(StatusProcess_CHOICES),
        "config_path_work": config_path_work
    })
    return render_to_response('search/diptable.html', locals(), context_instance=context)

@login_required
@csrf_exempt
def submit_order(request):
    print 'received request' + request.method
    validator = XmlValidation()

    #{ "order_title" : "example title", "aip_identifiers" : [ "b7738768-032d-3db1-eb42-b09611e6e6c6", "916c659c-909d-ad94-2289-c7ee8e7482d9"]}
    if request.method == 'POST':
        order_json = json.loads(request.body)

        if "order_title" not in order_json:
            response = {'process_id' : None, 'error' : "Missing order_title element in order request."}
            return HttpResponse(json.dumps(response))
        if "aip_identifiers" not in order_json:
            response = {'process_id' : None, 'error' : "Missing aip_identifiers element in order request."}
            return HttpResponse(json.dumps(response))

        order_title = order_json["order_title"]
        aip_identifiers = order_json["aip_identifiers"]

        # verify that all necessary AIPs exist return error otherwise
        for aip_identifier in aip_identifiers:
           if InformationPackage.objects.filter(identifier=aip_identifier).count() == 0:
                response = {'process_id' : None, 'error' : "Unknown IP for provided UUID %s" % aip_identifier}
                return HttpResponse(json.dumps(response))
        try:
            dip = DIP.objects.create(name=order_title)
        except Exception as e:
            response = {'process_id' : None, 'error' : repr(e)}
            return HttpResponse(json.dumps(response))

        process_id = getUniqueID()
        wf = WorkflowModules.objects.get(identifier = AIPtoDIPReset.__name__)
        InformationPackage.objects.create(path=os.path.join(config_path_work, process_id), uuid=process_id, statusprocess=0, packagename=order_title, last_task=wf)
        print "Created DIP with UUID %s" % aip_identifier

        for aip_identifier in aip_identifiers:
            # if entry does not exist in search_aip add it from earkweb_informationpackage
            if AIP.objects.filter(identifier=aip_identifier).count() == 0:
                ip = InformationPackage.objects.get(identifier=aip_identifier)
                aip = AIP.objects.create(identifier=aip_identifier, cleanid="", source=ip.storage_loc, date_selected=timezone.now())

            aip = AIP.objects.get(identifier=aip_identifier)
            Inclusion(aip=aip, dip=dip).save()
            print "Added existing package %s" % aip_identifier

        response = {"process_id": process_id, 'status': 'Submitted'}
        return HttpResponse(json.dumps(response))
    else:
        response = {'process_id' : None, 'error' : "Unsupported GET request."}
        return HttpResponse(json.dumps(response))

@login_required
@csrf_exempt
def order_status(request):
    print 'received request' + request.method

    if request.method == 'GET':
        if not 'process_id' in request.GET:
            response = {'process_id' : None, 'error' : "Missing HTTP request parameter process_id"}
            return HttpResponse(json.dumps(response))

        process_id = request.GET['process_id']
        if not process_id:
            response = {'process_id' : None, 'error' : "Empty HTTP request parameter process_id"}
            return HttpResponse(json.dumps(response))

        try:
            ip = InformationPackage.objects.get(uuid=process_id)
        except Exception as e:
            response = {'process_id' : process_id, 'error' : repr(e)}
            return HttpResponse(json.dumps(response))

        try:
            dip = DIP.objects.get(name=ip.packagename)
        except Exception as e:
            response = {'process_id' : process_id, 'error' : repr(e)}
            return HttpResponse(json.dumps(response))

        print "Found DIP for provided UUID %s = %s" % (process_id, dip.name)

        #stat_proc_choices = dict(StatusProcess_CHOICES)
        #print stat_proc_choices[ip.statusprocess]
        #response = {'process_status' : stat_proc_choices[ip.statusprocess], 'process_id' : process_id}

        response = {'process_id' : process_id, 'process_status' : "Progress", 'dip_storage' : ""}

        #if staus is ok try finding ip in storage and return
        if ip.statusprocess == 0:
            try:
                pts = PairtreeStorage(config_path_storage)
                package_object_path = pts.get_object_path(ip.identifier)
                if os.path.exists(package_object_path):
                    print 'Storage path: %s' % package_object_path
                    response['dip_storage'] = package_object_path

            except Exception as e:
                print "Storage path not found"
                #response = {'process_id' : process_id, 'error' : repr(e)}
                #return HttpResponse(json.dumps(response))

        return HttpResponse(json.dumps(response))
    else:
        response = {'process_id' : None, 'error' : "Unsupported POST request."}
        return HttpResponse(json.dumps(response))