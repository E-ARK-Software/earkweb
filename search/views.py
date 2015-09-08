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
from lxml import etree
import requests

from forms import SearchForm, UploadFileForm
from models import AIP, DIP, Inclusion
from query import get_query_string

from config.params import config_path_work
from earkcore.utils.stringutils import safe_path_string
from earkcore.utils.fileutils import mkdir_p
from django.views.decorators.csrf import csrf_exempt

from earkcore.utils.stringutils import lstrip_substring
from sip2aip.forms import PackageWorkflowModuleSelectForm

logger = logging.getLogger(__name__)

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
    print request.user
    dips = DIP.objects.all()
    template = loader.get_template('search/packsel.html')
    context = RequestContext(request, {
        'package_list': dips
    })
    return HttpResponse(template.render(context))


@login_required
def start(request):
    print request.user
    dips = DIP.objects.all()
    template = loader.get_template('search/start.html')
    context = RequestContext(request, {
        'package_list': dips
    })
    return HttpResponse(template.render(context))

@login_required
def dip(request, name):
    dip = DIP.objects.get(name=name)
    template = loader.get_template('search/dip.html')

    workflow_form = PackageWorkflowModuleSelectForm()

    context = RequestContext(request, {'dip': dip, 'uploadFileForm': UploadFileForm(), 'workflow_form': workflow_form})
    return HttpResponse(template.render(context))
    #return render_to_response('search/dip.html', {'dip': dip, 'uploadFileForm': UploadFileForm()})

@login_required
def aip(request, dip_name, identifier):
    dip = DIP.objects.get(name=dip_name)
    aip = dip.aips.get(identifier=identifier)
    template = loader.get_template('search/aip.html')
    context = RequestContext(request, {'dip': dip, 'aip': aip})
    return HttpResponse(template.render(context))

@login_required
def demosearch(request):
    print request.user
    template = loader.get_template('search/demosearch.html')
    context = RequestContext(request, {
        
    })
    return HttpResponse(template.render(context))

@login_required
def demosearch_govdocs(request):
    print request.user
    template = loader.get_template('search/demosearch_govdocs.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
def demosearch_news(request):
    print request.user
    template = loader.get_template('search/demosearch_news.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

@login_required
def demosearch_package(request):
    print request.user
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
                #logger.debug("RESULT:\n" + docsjson)
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
def toggle_select_package(request):
    if request.method == "POST":
        if request.POST.__contains__("action") and request.POST["action"] == "search":
            return search_form(request)
        else:
            identifier = request.POST["identifier"]
            cleanid = request.POST["cleanid"]
            dip_name = request.POST["dip"]
            dip = DIP.objects.get(name=dip_name)
            if request.POST["action"] == "add":
                if AIP.objects.filter(identifier=identifier).count() == 0:
                    aip = AIP.objects.create(identifier=identifier, cleanid=cleanid, source="unknown", date_selected=timezone.now())
                    Inclusion(aip=aip, dip=dip).save()
                    logger.debug("Added new package %s" % identifier)
                elif dip.aips.filter(identifier=identifier).count() == 0:
                    aip = AIP.objects.filter(identifier=identifier)[0]
                    Inclusion(aip=aip, dip=dip).save()
                    logger.debug("Added existing package %s" % identifier)
                else:
                    logger.debug("Package %s added already" % identifier)
            elif request.POST["action"] == "rem":
                aip = AIP.objects.filter(identifier=identifier)[0]
                Inclusion.objects.filter(aip=aip, dip=dip).delete()
                logger.debug("Removed package %s" % identifier)
            return HttpResponse("{ \"success\": \"true\" }")
    else:
        return render(request, 'search/index.html')
    
@login_required
def get_file_content(request, lily_id):
    logger.debug("Get content for lily_id %s" % lily_id)
    if request.is_ajax():
        query_url =  settings.SERVER_REPO_RECORD_CONTENT_QUERY.format(lily_id)
        logger.debug("Get file content query: %s" % query_url)
        r = requests.get(query_url, stream=True)
        logger.debug("Get file content query status code: %d" % r.status_code)
        logger.debug("Get file content query content-type: %s" % r.headers['content-type'])
        contentType = r.headers['content-type']
        response_content = r.text
        response_content_utf8 = response_content.encode("utf-8")
        #if contentType == 'image/jpeg': 
        #    with open('/home/shs/test.jpeg', 'wb') as f:
        #        for chunk in r.iter_content(1024):
        #            f.write(chunk)
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
            DIP.objects.create(name=dip_creation_process_name)
            return HttpResponseRedirect(reverse('search:packsel'))
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
        r = requests.get(settings.SERVER_HDFS_AIP_QUERY.format(filename))
        with open('working_area/' + filename, 'w') as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
        extractTar(filename)

def extractTar(filename):
    with tarfile.open('working_area/' + filename) as tar:
        tar.extractall('working_area/')

