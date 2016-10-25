from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from config.configuration import access_solr_server_ip
from django.views.generic.list import ListView
from earkcore.models import InformationPackage
from django.utils.decorators import method_decorator
from workers.tasks import LilyHDFSUpload
from config.configuration import storage_solr_server_ip
from config.configuration import access_solr_port
from config.configuration import lily_content_access_ip
from config.configuration import lily_content_access_port
from config.configuration import earkweb_version
from config.configuration import earkweb_version_date
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig

def public_search(request):
    print request.user
    template = loader.get_template('earkweb/pubsearch.html')
    context = RequestContext(request, {
        'access_solr_server_ip': access_solr_server_ip,
        'access_solr_port': access_solr_port,
        'lily_content_access_ip': lily_content_access_ip,
        'lily_content_access_port': lily_content_access_port,
    })
    return HttpResponse(template.render(context))

@login_required
def home(request):
    print request.user
    template = loader.get_template('earkweb/home.html')
    context = RequestContext(request, {
        'earkweb_version': earkweb_version,
        'earkweb_version_date': earkweb_version_date,
    })
    return HttpResponse(template.render(context))


@login_required
def version(request):
    print request.user
    template = loader.get_template('earkweb/version.html')
    context = RequestContext(request, {

    })
    return HttpResponse(template.render(context))

class IndexingStatusTable(tables.Table):

    from django_tables2.utils import A

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s")
    uuid = tables.LinkColumn('sip2aip:working_area', kwargs={'section': 'sip2aip', 'uuid': A('uuid')})
    packagename = tables.LinkColumn('sip2aip:ip_detail', kwargs={'pk': A('pk')})

    class Meta:
        model = InformationPackage
        fields = ('identifier', 'packagename', 'uuid', 'last_change', 'last_task', 'statusprocess', 'num_indexed_docs')
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

# class IndexingStatusList(ListView):
#     """
#     Processing status
#     """
#     model = InformationPackage
#     template_name = 'earkweb/indexing_status.html'
#     context_object_name = 'ips'
#
#     queryset=InformationPackage.objects.extra(where=["identifier!='' and last_task_id='%s'" % LilyHDFSUpload.__name__]).order_by('last_change')
#
#     @method_decorator(login_required)
#     def dispatch(self, *args, **kwargs):
#         return super(IndexingStatusList, self).dispatch(*args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super(IndexingStatusList, self).get_context_data(**kwargs)
#         return context
