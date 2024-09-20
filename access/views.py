import json
import traceback
import logging

import xmltodict
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django_tables2 import RequestConfig
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.template import loader
from django.http import JsonResponse
import django_tables2 as tables
from django.utils.safestring import mark_safe
import requests
from django.contrib.auth.models import User

from config.configuration import solr_host, django_backend_service_host, django_backend_service_port, \
    verify_certificate, config_path_work, solr_core_url, solr_core_ping_url, django_service_url
from config.configuration import django_service_port
from config.configuration import django_service_host
from config.configuration import solr_core
from config.configuration import solr_port
from config.configuration import config_path_storage
from earkweb.models import InformationPackage, Representation

from django.utils.translation import gettext_lazy as _



from util.djangoutils import error_resp, get_user_api_token
from util import service_available

logger = logging.getLogger(__name__)


@login_required
def index(request):
    template = loader.get_template('access/index.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


def indexingstatus(request):
    """
    Indexing Status Table view
    """
    if not service_available(solr_core_ping_url):
        return render(request, 'earkweb/error.html', {'header': 'SolR server unavailable', 'message': "Required service is not available at: %s" % solr_core_ping_url})
    # pylint: disable-next=no-member
    queryset=InformationPackage.objects.extra(where=["storage_dir != ''"]).order_by('-last_change')
    table = IndexingStatusTable(queryset)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)
    return render(request, 'access/indexing_status.html', {'informationpackage': table})


class IndexingStatusTable(tables.Table):

    from django_tables2.utils import A

    identifier = tables.LinkColumn('access:asset', args={A('identifier')}, verbose_name=_('Identifier'))

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name=_('Last change'))
    num_indexed_docs_storage = tables.Column(verbose_name=_('Number of indexed documents'))

    class Meta:
        model = InformationPackage
        fields = ('identifier', 'last_change', 'num_indexed_docs_storage')
        attrs = {'class': 'paleblue table table-striped table-bordered table-condensed'}
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_num_indexed_docs_storage(value):
        return mark_safe('<b>%s</b>' % value)


class InformationPackageDetail(DetailView):
    """
    Information Package Detail View
    """
    model = InformationPackage
    context_object_name = 'ip'
    template_name = 'management/detail.html'
    slug_field = 'identifier'
    slug_url_kwarg = 'identifier'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InformationPackageDetail, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InformationPackageDetail, self).get_context_data(**kwargs)
        context['config_path_work'] = config_path_work
        # pylint: disable-next=no-member
        distributions = Representation.objects.filter(ip_id=self.object.pk).values()
        context['distributions'] = distributions
        return context


@login_required
def search(request):
    template = loader.get_template('access/search.html')
    context = {
        'local_solr_server_ip': solr_host,
        'django_service_host': django_service_host,
        'django_service_port': django_service_port,
        'local_solr_port': solr_port,
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def get_information_package_item(request, identifier, entry):

    entry_without_id = entry.replace(identifier+"/", "")

    tar_entry = entry_without_id

    logging.debug("Storage path: %s" % config_path_storage)
    logging.debug("Data asset: %s " % identifier)
    logging.debug("Entry path: %s " % tar_entry)

    url = "%s/api/ips/%s/%s/stream" % (django_service_url, identifier, tar_entry)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    if response.status_code == 404:
        return render(request, 'earkweb/error.html',
                      {'header': 'Not available',
                       'message': "Resource not found!"})
    elif response.status_code == 200:
        content_type = response.headers['content-type']
        if content_type == "application/pdf":
            search_term = request.GET["search"] if "search" in request.GET else None
            import base64
            base64_encoded = base64.b64encode(response.content)
            base64_string = base64_encoded.decode("ascii")
            return render(request, 'access/pdfviewer.html', {'url': url, "search": search_term, 'data': base64_string})
        if content_type.startswith('text'):
            content_type = '%s; charset=utf-8' % content_type
        print(content_type)
        return HttpResponse(response.content, content_type=content_type)
    else:
        return render(request, 'earkweb/error.html',
                      {'header': 'An error occurred',
                       'message': "An error occurred when trying to retrieve the entry: %s" % tar_entry})



@login_required
def reindex_storage(request):
    """
    @type request: django.core.handlers.wsgi.WSGIRequest
    @param request: Request
    @rtype: django.http.JsonResponse
    @return: JSON response (task state metadata)
    """
    data = {"success": False, "errmsg": "undefined"}
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            #job = index_aip_storage.delay(dir)
            #data = {"success": True, "id": job.id}
            return {}
    except Exception as err:
        data = {"success": False, "errmsg": str(err)}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)
