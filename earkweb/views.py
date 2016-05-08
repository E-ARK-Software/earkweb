from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from config.configuration import access_solr_server_ip
from django.views.generic.list import ListView
from earkcore.models import InformationPackage
from django.utils.decorators import method_decorator
from workers.tasks import LilyHDFSUpload
from config.configuration import local_solr_server_ip

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


class IndexingStatusList(ListView):
    """
    Processing status
    """
    model = InformationPackage
    template_name = 'earkweb/indexing_status.html'
    context_object_name = 'ips'

    queryset=InformationPackage.objects.extra(where=["identifier!='' and last_task_id='%s'" % LilyHDFSUpload.__name__]).order_by('last_change')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IndexingStatusList, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexingStatusList, self).get_context_data(**kwargs)
        return context
