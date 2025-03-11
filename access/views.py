import json
import traceback
import logging

import xmltodict
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django_tables2 import RequestConfig
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.template import loader
from django.http import JsonResponse
import django_tables2 as tables
from django.utils.safestring import mark_safe
from requests.auth import HTTPBasicAuth
import requests
from django.contrib.auth.models import User

from config.configuration import solr_host, django_backend_service_host, django_backend_service_port, \
    verify_certificate, config_path_work, solr_core_url, solr_core_ping_url, django_service_url
from config.configuration import django_service_port
from config.configuration import django_service_host
from config.configuration import solr_core
from config.configuration import solr_port
from config.configuration import config_path_storage
from config.configuration import flower_service_url
from config.configuration import flower_user
from config.configuration import flower_password
from config.configuration import django_backend_service_api_url, verify_certificate

from earkweb.models import InformationPackage, Representation

from django.utils.translation import gettext_lazy as _



from util.djangoutils import error_resp, get_user_api_token
from util import service_available

from celery.result import AsyncResult


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
    return render(request, 'access/indexing_status.html', {
        'informationpackage': table,
        'flower_service_url': flower_service_url,
        'flower_user': flower_user,
        'flower_password': flower_password
    })

@login_required
@csrf_exempt
def informationpackages_overview(request):
    area = "access"
    areacode = "1"
    filterword = request.POST['filterword'] if 'filterword' in request.POST.keys() else ""
    sql_query = """
    select ip.id as id, ip.work_dir as path, ip.uid as uid, ip.package_name as package_name, 
    ip.identifier as identifier,
    CONCAT('<a href="/earkweb/submission/upload_step1/',ip.id,'/" data-toggle="tooltip" title="Change">
    <i class="fas fa-edit editcol"></i></a>') as edit,
    CONCAT('<a href="/earkweb/submission/ips/',ip.id,'/startingest" data-toggle="tooltip" title="Ingest">
    <i class="fas fa-box editcol"></i></a>') as ingest,
    CONCAT('<a href="/earkweb/submission/delete/',ip.id,'/" data-toggle="tooltip" title="Delete">
    <i class="fas fa-trash editcol"></i></a>') as delcol 
    from informationpackage as ip
    where 
    (ip.uid like '%%{0}%%' or ip.package_name like '%%{0}%%' or ip.identifier like '%%{0}%%')
    and deleted != 1
    order by ip.last_change desc;
    """.format(filterword, areacode)
    # user_id={0} and, request.user.pk
    # pylint: disable-next=no-member
    queryset = InformationPackage.objects.raw(sql_query)
    table = IndexingStatusTable(queryset)
    RequestConfig(request, paginate={'per_page': 8}).configure(table)
    context = {
        'informationpackage': table,
    }
    if request.method == "POST":
        return render(request, 'earkweb/ipstable.html', context=context)
    else:
        return render(request, '%s/overview.html' % area, {'informationpackage': table})


class IndexingStatusTable(tables.Table):

    from django_tables2.utils import A

    identifier = tables.LinkColumn('access:asset', args={A('identifier')}, verbose_name=_('Identifier'))

    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name=_('Last change'))
    num_indexed_docs_storage = tables.Column(verbose_name=_('Indexed'))
    indexing_action = tables.TemplateColumn(template_name='access/action_buttons.html', verbose_name=_('Action'), orderable=False)
    indexing_status = tables.TemplateColumn(template_name='access/indexing_status_div.html', verbose_name=_('Status'), orderable=False)

    class Meta:
        model = InformationPackage
        fields = ('identifier', 'last_change', 'num_indexed_docs_storage', 'indexing_action')
        attrs = {'class': 'paleblue table table-striped table-bordered table-condensed'}
        row_attrs = {'data-id': lambda record: record.pk}

    def render_num_indexed_docs_storage(self, value, record):
        """Render number of indexed docs with record information"""
        pk = record.pk  # Access the primary key of the current record
        return mark_safe(f'<b id="val-{pk}">{value}</b>')
    
    def render_indexing_action(self, record):
        """Render button"""
        print(f"Rendering indexing action for record: {record.pk}") 
        button_html = render_to_string('access/indexing_status_button.html', {'record': record})
        return mark_safe(button_html)
    
    def render_indexing_status(self, record):
        """Render status div"""
        print(f"Rendering indexing action for record: {record.pk}") 
        status_div_html = render_to_string('access/indexing_status_div.html', {'record': record})
        return mark_safe(status_div_html)


import time
import requests
from requests.auth import HTTPBasicAuth
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def start_indexing(request, pk):
    logger.info(f"start_indexing called, pk: {pk}")
    try:
        # Fetch InformationPackage instance
        ip = InformationPackage.objects.get(id=pk)
        
        # Prepare external API URL for indexing
        url = f"{django_service_url}/api/ips/{ip.identifier}/index/"
        logger.info(f"Indexing URL: {url}")
        
        # Get user API token for authorization
        user_api_token = get_user_api_token(request.user)
        
        # Send request to external API to start indexing
        response = requests.post(url, headers={'Authorization': f'Token {user_api_token}'}, verify=verify_certificate)
        
        if response.status_code != 201:
            return JsonResponse(response.json(), status=response.status_code)

        # Assuming the external API response includes a Celery task ID (job_id) 
        job_id = response.json().get('job_id')
        if not job_id:
            return JsonResponse({"message": "Job ID not found in response"}, status=500)

        # Flower task info URL
        flower_url = f'{flower_service_url}api/task/info/{job_id}'
        
        # Retry fetching task info from Flower
        max_retries = 5
        delay = 2  # Start with a 2-second delay
        for attempt in range(max_retries):
            flower_response = requests.get(flower_url, auth=HTTPBasicAuth(flower_user, flower_password))

            if flower_response.status_code == 200:
                task_info = flower_response.json()
                return JsonResponse({
                    "message": "Indexing started",
                    "job_id": job_id,
                    "status": task_info.get('state'),
                    "info": task_info
                })
            elif flower_response.status_code == 404:
                # Task not yet registered, wait and retry
                logger.info(f"Task not found in Flower, retrying... (attempt {attempt + 1})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                return JsonResponse({
                    "message": "Indexing started but failed to fetch status from Flower.",
                    "job_id": job_id,
                    "flower_error": flower_response.text
                }, status=flower_response.status_code)
        
        # If we exhaust retries without success
        return JsonResponse({
            "message": "Indexing started but task info could not be fetched from Flower.",
            "job_id": job_id,
            "error": "Task not found after retries."
        }, status=404)
        
    except InformationPackage.DoesNotExist:
        return JsonResponse({"message": "Information package does not exist"}, status=404)
    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}")
        return JsonResponse({"message": "Internal server error"}, status=500)



def indexing_task_status(request, task_id):
    """Get celery task status from flower"""
    # Flower task info URL
    flower_url = f'{flower_service_url}api/task/info/{task_id}'
    
    # Flower authentication details (replace with your actual credentials)
    # flower_user = f'{flower_user}'
    # flower_password = f'{flower_password}'

    try:
        # Make an authenticated GET request to Flower's API to get task status
        response = requests.get(flower_url, auth=HTTPBasicAuth(flower_user, flower_password))
        
        # If the request is successful, pass the data back as JSON
        if response.status_code == 200:
            task_info = response.json()
            return JsonResponse({
                "status": task_info.get('state'),
                "result": task_info.get('result'),
                "info": task_info
            })
        else:
            return JsonResponse({"error": "Failed to fetch task status from Flower."}, status=response.status_code)

    except requests.exceptions.RequestException as e:
        # Handle any network-related errors
        return JsonResponse({"error": str(e)}, status=500)
    

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


def landing_page(request, identifier):
    """
    Fetch metadata using the API and display public file resources.
    """
    # Fetch metadata from the API
    metadata_url = f"{django_backend_service_api_url}/ips/{identifier}/file-resource/metadata/metadata.json"
    response = requests.get(metadata_url)

    if response.status_code != 200:
        raise Http404("Metadata not found")

    metadata = response.json()

    # Extract metadata fields
    title = metadata.get("title", "Untitled Package")
    description = metadata.get("description", "No description available.")

    # Extract publicly available files and preview image
    public_files = []
    preview_image = None

    for repkey, repdata in metadata.get("representations", {}).items():
        for filename, file_data in repdata.get("file_metadata", {}).items():
            file_path = f"representations/{repkey}/data/{filename}"
            if file_data.get("isPublicAccess", False):
                file_description = file_data.get("description", filename)  # Use description if available
                public_files.append({"path": file_path, "description": file_description})
                if file_data.get("isPreview", False):
                    preview_image = file_path

    # Get custom stylesheet from query parameters
    stylesheet = request.GET.get("stylesheet", None)

    return render(request, "access/package_files.html", {
        "identifier": identifier,
        "title": title,
        "description": description,
        "preview_image": preview_image,
        "public_files": public_files,
        "stylesheet": stylesheet
    })


def disseminate(request, identifier, entry):
    """
    disseminate
    """
    logging.debug("Storage path: %s" % config_path_storage)
    logging.debug("Data asset: %s " % identifier)
    logging.debug("Entry path: %s " % entry)

    url = f"{django_service_url}/api/ips/{identifier}/file-resource/{entry}/"
    response = requests.get(url)
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
                       'message': "An error occurred when trying to retrieve the entry: %s" % entry})


@login_required
@csrf_exempt
def get_information_package_item(request, identifier, entry):

    logging.debug("Storage path: %s" % config_path_storage)
    logging.debug("Data asset: %s " % identifier)
    logging.debug("Entry path: %s " % entry)

    url = f"{django_service_url}/api/ips/{identifier}/file-item/{entry}/"
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
                       'message': "An error occurred when trying to retrieve the entry: %s" % entry})



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



@login_required
def index_package(request):
    template = loader.get_template('access/index_package.html')
    context = {
        
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def num_indexed(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    context = {
        'num_indexed': ip.num_indexed_docs_storage
    }
    template = loader.get_template('access/num_index_value.html')
    return HttpResponse(template.render(context=context, request=request)) 
