import os
import functools
import json
import logging
import tarfile
from threading import Thread
import traceback
import urllib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext, loader
from django.utils import timezone
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from lxml import etree
import requests

from forms import SearchForm, UploadFileForm
from models import AIP, DIP, Inclusion
from query import get_query_string

from config.configuration import config_path_work
from earkcore.utils.stringutils import safe_path_string
from earkcore.utils.fileutils import mkdir_p
from django.views.decorators.csrf import csrf_exempt

from earkcore.utils.stringutils import lstrip_substring
from sip2aip.forms import AIPtoDIPWorkflowModuleSelectForm
from earkcore.models import InformationPackage
from earkcore.utils.randomutils import getUniqueID
from workflow.models import WorkflowModules

logger = logging.getLogger(__name__)
from django.shortcuts import render_to_response
from earkcore.models import StatusProcess_CHOICES
from earkcore.filesystem.fsinfo import path_to_dict
from workers.tasks import AIPtoDIPReset

from earkcore.xml.xmlvalidation import XmlValidation
from io import BytesIO
import lxml
from config.configuration import server_hdfs_aip_query

from config.configuration import server_repo_record_content_query

@login_required
def index(request, procname):
    if DIP.objects.count() == 0:
        DIP.objects.create(name='DIP 1')
    template = loader.get_template('search/index.html')
    form = SearchForm()
    context = RequestContext(request, {
        'form':form,
        'dips':DIP.objects.all(),
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
            start = 0
            rows = 20
            query_string = get_query_string(keyword, content_type, start, rows)
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
                    responseObj['lily_id'] = urllib.quote_plus(doc["lily.id"])
                    responseObj['contentType'] = doc["contentType"]
                    responseObj['size'] = doc["size"]
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
            dip = DIP.objects.create(name=dip_creation_process_name)
            uuid = getUniqueID()
            wf = WorkflowModules.objects.get(identifier = AIPtoDIPReset.__name__)
            InformationPackage.objects.create(path=os.path.join(config_path_work, uuid), uuid=uuid, statusprocess=0, packagename=dip_creation_process_name, last_task=wf)
            url = reverse('search:dip', args=(dip.name,))
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
    if request.method == 'POST':
        order_xml = BytesIO(request.body)
        parsed_order_xml = lxml.etree.parse(order_xml)
        parsed_order_schema = lxml.etree.parse("./earkcore/xml/resources/order.xsd")
        result = validator.validate_XML(parsed_order_xml, parsed_order_schema)
        root = parsed_order_xml.getroot()

        # verify that all necessary AIPs exist return error otherwise
        for child in root.iterchildren('UnitOfDescription'):
            aip_identifier = child.iterchildren('ReferenceCode').next().text
            if AIP.objects.filter(identifier=aip_identifier).count() == 0:
                return HttpResponse("Unknown AIP for provided UUID %s" % aip_identifier)


        order_title = root.iterchildren('OrderTitle').next().text
        dip = DIP.objects.create(name=order_title)
        uuid = getUniqueID()
        wf = WorkflowModules.objects.get(identifier = AIPtoDIPReset.__name__)
        InformationPackage.objects.create(path=os.path.join(config_path_work, uuid), uuid=uuid, statusprocess=0, packagename=order_title, last_task=wf)
        print "Created DIP with UUID %s" % aip_identifier

        for child in root.iterchildren('UnitOfDescription'):
            aip_identifier = child.iterchildren('ReferenceCode').next().text
            aip = AIP.objects.get(identifier=aip_identifier)
            Inclusion(aip=aip, dip=dip).save()
            print "Added existing package %s" % aip_identifier

        return HttpResponse(uuid)
    else:
        return HttpResponse("Unsupported GET request.")

@login_required
@csrf_exempt
def order_status(request):
    print 'received request' + request.method
    if request.method == 'POST':
        pkg_uuid = request.POST['pkg_uuid']
        ip = InformationPackage.objects.get(uuid=pkg_uuid)
        dip = DIP.objects.get(name=ip.packagename)
        print "Found DIP for provided UUID %s = %s" % (pkg_uuid, dip.name)

        stat_proc_choices = dict(StatusProcess_CHOICES)
        print stat_proc_choices[ip.statusprocess]
        return HttpResponse(stat_proc_choices[ip.statusprocess])
    else:
        return HttpResponse("Unsupported GET request.")