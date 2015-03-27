from django.template import RequestContext, loader
from django.http import HttpResponse
import urllib
import json

import requests
from django.http import HttpResponseBadRequest
from django.http import HttpResponseServerError
from django.shortcuts import render
from models import Package
from forms import SearchForm

from django.conf import settings
from django.utils import timezone
import logging
import traceback

logger = logging.getLogger(__name__)

def index(request):
    template = loader.get_template('search/index.html')
    form = SearchForm()
    context = RequestContext(request, {
        'form':form
    })
    return HttpResponse(template.render(context))

def search_form(request):
    if request.POST:
        form = SearchForm(request.POST)
        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            query_string = settings.SERVER_SOLR_QUERY_URL.format(keyword)
            logger.debug("Solr query string: %s" % query_string)
            try: 
                response = requests.get(query_string)
                docs = response.json()["response"]["docs"]  
                documents = list()
                for doc in docs:
                    responseObj = dict()
                    responseObj['title'] = doc["path"]
                    responseObj['lily_id'] = urllib.quote_plus(doc["lily.id"])
                    responseObj['contentType'] = doc["contentType"]
                    # get package property from path
                    packageSep = doc["path"].find("/")
                    if(packageSep != -1):
                        responseObj['pack'] = doc["path"][0:packageSep]
                    else:
                        responseObj['pack'] = "Unknown"
                    if responseObj['lily_id'] != "":
                        documents.append(responseObj)
                docsjson = json.dumps(documents, indent=4)
                logger.debug("RESULT:\n" + docsjson)
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
    
def toggle_select_package(request):
    if request.POST:
        if request.is_ajax():
            identifier = request.POST["identifier"]
            cleanid = request.POST["cleanid"]
            if request.POST["action"] == "add":
                if(Package.objects.filter(identifier = identifier).count() == 0):
                    Package.objects.create(identifier=identifier, cleanid=cleanid, source="unknown", date_selected=timezone.now())
                    logger.debug("Added package %s" % identifier)
                else:
                    logger.debug("Package %s added already" % identifier)
            elif request.POST["action"] == "rem":
                Package.objects.filter(identifier = identifier).delete()
                logger.debug("Removed package %s" % identifier)
            return HttpResponse("{ \"success\": \"true\" }")
    else:
        return render(request, 'search/index.html')
    

def get_file_content(request, lily_id):
    logger.debug("Get content for lily_id %s" % lily_id)
    if request.is_ajax():
        query_url =  settings.SERVER_REPO_RECORD_CONTENT_QUERY.format(lily_id)
        logger.debug("Get file content query: %s" % query_url)
        r = requests.get(query_url)
        logger.debug("Get file content query status code: %d" % r.status_code)
        logger.debug("Get file content query content-type: %s" % r.headers['content-type'])
        return HttpResponse(r.text)
    else:
        pass