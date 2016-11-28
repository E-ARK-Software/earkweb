from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView
from earkcore.models import InformationPackage
from django.utils.decorators import method_decorator
from workers.tasks import LilyHDFSUpload
from config.configuration import storage_solr_server_ip
from config.configuration import access_solr_port, access_solr_core, access_solr_server_ip
from config.configuration import lily_content_access_ip
from config.configuration import lily_content_access_port
from config.configuration import earkweb_version
from config.configuration import earkweb_version_date
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig
from workers.tasks import AIPIndexing, AIPStore, IPClose, DIPStore, IPDelete, SolrUpdateCurrentMetadata
from earkcore.utils.serviceutils import service_available

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


def indexingstatus(request):
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
    queryset=InformationPackage.objects.extra(where=["storage_loc != ''"]).order_by('-last_change')
    table = IndexingStatusTable(queryset)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    return render(request, 'sip2aip/indexing_status.html', {'informationpackage': table})


class IndexingStatusTable(tables.Table):

    from django_tables2.utils import A

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s")
    uuid = tables.LinkColumn('sip2aip:working_area', kwargs={'section': 'sip2aip', 'uuid': A('uuid')})
    #packagename = tables.LinkColumn('sip2aip:ip_detail', kwargs={'pk': A('pk')})
    num_indexed_docs = tables.Column(verbose_name='Number of indexed documents')

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
