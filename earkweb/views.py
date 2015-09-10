from django.http import HttpResponse
from django.template import RequestContext, loader

def public_search(request):
    print request.user
    template = loader.get_template('earkweb/pubsearch.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))