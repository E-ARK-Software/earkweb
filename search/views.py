from django.template import RequestContext, loader
from django.http import HttpResponse
import urllib
import json

import requests
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from models import Package
from forms import SearchForm

from django.conf import settings
from django.utils import timezone

def index(request):
    
    template = loader.get_template('search/index.html')
    form = SearchForm()
    context = RequestContext(request, {
        'form':form
    })
    return HttpResponse(template.render(context))

def article(request, article_id):
    
    url = settings.RECORD_URL + urllib.quote_plus(article_id)
    print "URL:\n" + url
    response = requests.get(url)
    
    jsonResult = json.dumps(response.json(), sort_keys=True, indent=4, separators=(',', ': '))
    print "RESULT:\n" + jsonResult
    data = json.loads(jsonResult)
    
    article_headline = "unknown"
    try:
        article_headline = data["fields"]["ns1$headline"]
    except KeyError:
        pass
    
    article_author = "unkown"
    try:
        article_author = data["fields"]["ns1$author"]
    except KeyError:
        pass
    
    article_body = "empty"
    try:
        article_body = data["fields"]["ns1$articleBody"]
    except KeyError:
        pass
            
    
    template = loader.get_template('search/article.html')
    context = RequestContext(request, {
        'article_headline': article_headline,
        'article_author': article_author,
        'article_body': article_body,
    })
    return HttpResponse(template.render(context))

def search_form(request):
    if request.POST:
        form = SearchForm(request.POST)
        if form.is_valid():
            
            keyword = form.cleaned_data['keyword']
            query_string = settings.SOLR_QUERY_URL.format(keyword)
            
            print "QUERY STRING:\n" + query_string
            
            try: 
                response = requests.get(query_string)
                docs = response.json()["response"]["docs"]  
                documents = list()
                
                count = 1;
                for doc in docs:
                    a = dict()
                    a['title'] = doc["path"]
                    a['lily_id'] = urllib.quote_plus(doc["lily.id"])
                    a['contentType'] = doc["contentType"]
                    # simulated package property
                    packageSep = doc["path"].find("/")
                    if(packageSep != -1):
                        a['pack'] = doc["path"][0:packageSep]
                    else:
                        a['pack'] = "Unknown"
                    if a['lily_id'] != "":
                        documents.append(a)
                    count += 1
                
                docsjson = json.dumps(documents, indent=4)
                
                print "RESULT:\n" + docsjson
            
            except KeyError, err:
                
                err_dict = {}
                err_dict["error"] = "Error processing request"
                
                print str(err)
                return HttpResponseBadRequest(json.dumps(err_dict))

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

def toggle_select_aip(request):
    if request.POST:
        if request.is_ajax():
            identifier = request.POST['identifier']
            source = "test"
            if(Package.objects.filter(identifier = identifier).count() == 0):
                Package.objects.create(identifier=identifier, source=source, date_selected=timezone.now())
            else:
                Package.objects.filter(identifier = identifier).delete()

            return HttpResponse("{ \"success\": \"true\" }")
    else:
        return render(request, 'search/index.html')
    
def toggle_select_package(request):
    if request.POST:
        if request.is_ajax():
            for infoitem in request.POST:
                print infoitem
            return HttpResponse("{ \"success\": \"true\" }")
    else:
        return render(request, 'search/index.html')
    
