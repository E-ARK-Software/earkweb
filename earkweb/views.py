from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from config.configuration import access_solr_server_ip

def public_search(request):
    print request.user
    template = loader.get_template('earkweb/pubsearch.html')
    context = RequestContext(request, {
        'server_ip': access_solr_server_ip,
    })
    return HttpResponse(template.render(context))

@login_required
def home(request):
    print request.user
    template = loader.get_template('earkweb/home.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))


@login_required
def version(request):
    print request.user
    template = loader.get_template('earkweb/version.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))