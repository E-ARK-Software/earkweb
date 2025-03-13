import json
import re
import os
import io
from collections import defaultdict
import traceback
import logging
from datetime import datetime, timedelta
from urllib.parse import unquote, urlencode, urlparse
import pysolr
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from django.shortcuts import redirect, render
from django.utils import translation
from django.views.generic.base import View
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
from django.http import JsonResponse
from django.utils.translation import gettext as trans
from celery.result import AsyncResult
from chartjs.views.lines import BaseLineChartView
from util import service_available
from util.djangoutils import get_user_api_token
from earkweb.models import InformationPackage
from eatb.pairtree_storage import make_storage_data_directory_path
from eatb.utils.datetime import get_date_from_iso_str, DT_ISO_FORMAT
from eatb.utils.fileutils import path_to_dict, from_safe_filename
from config.configuration import config_path_work, config_path_storage, verify_certificate
from config.configuration import sw_version, django_backend_service_api_url
from config.configuration import sw_version_date
from config.configuration import solr_host
from config.configuration import solr_port
from config.configuration import solr_core
from config.configuration import solr_core_ping_url
from config.configuration import solr_core_url


logger = logging.getLogger(__name__)


def get_domain_scheme(referrer):
    """
    Extract the scheme and domain from a given URL.

    This function takes a URL string as input and uses the `urlparse` function from 
    the `urllib.parse` module to parse the URL. It then extracts and returns the 
    scheme (e.g., 'http', 'https') and the domain (netloc) of the URL.

    Parameters:
    - referrer (str): The URL from which the scheme and domain need to be extracted.

    Returns:
    - tuple: A tuple containing the scheme and the domain (netloc) of the URL.

    Example:
    - If `referrer` is 'https://www.example.com/path', the function will return 
      ('https', 'www.example.com').
    """
    domain = urlparse(referrer)
    return domain.scheme, domain.netloc


class ActivateLanguageView(View):
    """
    View to handle changing the active language for the user session.

    Attributes:
        language_code (str): The language code to activate.
        redirect_to (str): The URL to redirect to after changing the language.
    """
    language_code = ''
    redirect_to = ''

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to change the active language.

        This method activates the specified language, updates the user session, 
        sets a cookie with the new language, and redirects the user to the 
        referring page or the current page if no referrer is found.

        Args:
            request (HttpRequest): The request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments, expected to contain 'language_code'.

        Returns:
            HttpResponse: A redirect response to the referring page or the current page.
        """
        self.redirect_to = request.META.get('HTTP_REFERER')
        self.language_code = kwargs.get('language_code')
        translation.activate(self.language_code)
        request.session['_language'] = self.language_code
        response = redirect(request.META.get('HTTP_REFERER', request.path_info))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, self.language_code)
        return response

from django.views.generic import TemplateView
from chartjs.views.lines import BaseLineChartView

def get_last_7_months_labels():
    months = ["January", "February", "March", "April", "May", "June", "July", 
              "August", "September", "October", "November", "December"]
    current_date = datetime.now()
    result = []
    
    for i in range(6, -1, -1):
        past_date = current_date - timedelta(days=i*30)
        month_year = months[past_date.month - 1] + " " + str(past_date.year % 100).zfill(2)
        result.append(month_year)
    
    return result

def get_last_7_months():
    months = ["January", "February", "March", "April", "May", "June", "July", 
              "August", "September", "October", "November", "December"]
    current_date = datetime.now()
    result = []
    date_ranges = []

    for i in range(6, -1, -1):
        past_date = current_date - timedelta(days=i*30)
        month_year = months[past_date.month - 1] + " " + str(past_date.year % 100).zfill(2)
        start_date = past_date.replace(day=1)
        end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
        result.append(month_year)
        date_ranges.append((start_date, end_date))
    
    return result, date_ranges

def get_entries_count_for_last_7_months(only_ingested=False):
    month_labels, date_ranges = get_last_7_months()
    counts = []
    for start_date, end_date in date_ranges:
        if only_ingested:
            # pylint: disable-next=no-member
            count = InformationPackage.objects.filter(
                created__range=(start_date, end_date)
            ).exclude(
                storage_dir__exact=''
            ).count()
        else:
            # pylint: disable-next=no-member
            count = InformationPackage.objects.filter(
                created__range=(start_date, end_date),
                storage_dir=''
            ).count()
        counts.append(count)
    
    return counts


class LineChartJSONView(BaseLineChartView):
    def get_labels(self):
        """Return 7 labels for the x-axis."""
        return get_last_7_months_labels()

    def get_providers(self):
        """Return names of datasets."""
        return ["Submitted", "Ingested"]

    def get_data(self):
        """Return 3 datasets to plot."""

        return [get_entries_count_for_last_7_months(only_ingested=False), get_entries_count_for_last_7_months(only_ingested=True)]


# Connect to your Solr server
solr = pysolr.Solr(solr_core_url, always_commit=True)


def get_mime_type_counts():
    # Query Solr to retrieve documents with content_type and path fields
    results = solr.search('content_type:* AND path:*', rows=1000)

    # Dictionary to count MIME types
    mime_type_counts = defaultdict(int)

    # Regular expression to extract the MIME type
    mime_type_regex = re.compile(r'^([^;]+)')
    
    # Regular expression to match the required path pattern
    path_regex = re.compile(r'representations/[^/]+/data/')

    # Process the results
    for result in results:
        # Get the 'path' field
        path = result.get('path')
        if path:
            # Check if the path matches the required structure
            if path_regex.search(path):
                # Get the first MIME type (if available) from 'content_type'
                content_type = result.get('content_type', [None])[0]
                if content_type:
                    # Extract the main MIME type
                    match = mime_type_regex.match(content_type)
                    if match:
                        mime_type = match.group(1)
                        mime_type_counts[mime_type] += 1

    # Prepare the labels and data lists for charting
    labels = list(mime_type_counts.keys())
    data = list(mime_type_counts.values())

    return {'labels': labels, 'data': data}






line_chart = TemplateView.as_view(template_name='earkweb/line_chart.html')
line_chart_json = LineChartJSONView.as_view()


def get_file_size_per_mime_type():
    # Query Solr to retrieve documents with content_type, path, and size fields
    results = solr.search('content_type:* AND path:*', rows=1000)

    # Initialize a dictionary to aggregate file sizes per MIME type
    mime_type_sizes = defaultdict(int)

    # Regular expression to extract the MIME type
    mime_type_regex = re.compile(r'^([^;]+)')
    
    # Regular expression to match the required path pattern
    path_regex = re.compile(r'representations/[^/]+/data/')

    # Process the results
    for result in results:
        path = result.get('path', None)
        if path:
            # Decode the path
            decoded_path = unquote(path.replace('=', '/'))
            if path_regex.search(decoded_path):
                content_type = result.get('content_type', [None])[0]
                size = result.get('size', 0)
                if content_type and size:
                    match = mime_type_regex.match(content_type)
                    if match:
                        mime_type = match.group(1)
                        mime_type_sizes[mime_type] += int(size)

    # Prepare the labels and data lists
    labels = list(mime_type_sizes.keys())
    data = list(mime_type_sizes.values())

    return {'labels': labels, 'data': data}


def clean_metadata(text):
    """
    Cleans the technical metadata from the input text and retains only the actual content.

    Parameters:
    text (str): The input string containing both metadata and content.

    Returns:
    str: Cleaned content text without technical metadata.
    """

    # Define a list of patterns to remove (date-time, access permissions, pdf metadata, etc.)
    patterns_to_remove = [
        r'\b[\w\-]+:.*',            # Metadata key-value pairs (e.g., pdf:PDFVersion, Last-Save-Date, etc.)
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',  # ISO date pattern (e.g., 2024-06-04T11:40:41Z)
        r'X-Parsed-By.*',           # Metadata parsing info
        r'meta:.*',                 # Meta-related fields
        r'producer.*',              # Producer info
        r'Pre',              # Producer info
        r'stream_.*',               # Stream info (size, source, etc.)
        r'n_.*',                    # Stream info (size, source, etc.)
        r'start_.*',                    # Stream info (size, source, etc.)
        r'end_.*',                    # Stream info (size, source, etc.)
        r'endnote_.*',                    # Stream info (size, source, etc.)
        r'annotation',                    # Stream info (size, source, etc.)
        r'body_.*',                    # Stream info (size, source, etc.)
        r'access_permission:.*',    # Access permission fields
        r'pdf:docinfo:.*',          # PDF docinfo metadata
        r'Content-Type.*',          # Content-Type fields
        r'xmp:.*',                  # XMP metadata
        r'xmpTPg:.*',               # XMP page info
        r'Creation-Date.*',         # Creation date fields
        r'\bcreated\b.*',           # Created fields
        r'\bmodified\b.*',          # Modified fields
    ]
    
    # Combine patterns into one regex
    combined_pattern = '|'.join(patterns_to_remove)
    
    # Remove all matching patterns from the text
    cleaned_text = re.sub(combined_pattern, '', text, flags=re.IGNORECASE)
    
    # Remove extra whitespaces, tabs, and newlines
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


class WordCloudView(View):
    def get(self, request, *args, **kwargs):
        # Initialize Solr client
        solr = pysolr.Solr(solr_core_url, timeout=10)

        
        # Define the filter query to match paths containing "representations", a UUID, and "data"
        filter_query = 'path:*/representations/*/data/*'
        
        # Fetch all documents with the "content" field
        results = solr.search('*:*', **{
            'fq': filter_query,     # Filter query to match the desired paths
             'fl': 'content,path',   # Retrieve both "content" and "path" fields
            'rows': 1000      # Fetch as many documents as you expect; modify as needed
        })

        # Aggregate all content fields into a single string
        logger.info(len(results))
        try:
            # Try to aggregate the content from all Solr documents
            all_content = ' '.join(
                [clean_metadata(' '.join(doc['content'])) if isinstance(doc.get('content', ''), list) else clean_metadata(doc.get('content', '')) 
                for doc in results]
            )
            
        except KeyError as e:
            # Handle the case where 'content' is missing in a document
            logger.error(f"KeyError: The 'content' field is missing in some documents: {e}")
            all_content = ''
        except TypeError as e:
            # Handle cases where 'results' is not iterable or contains invalid types
            logger.error(f"TypeError: Invalid type encountered in Solr results: {e}")
            all_content = ''
        except Exception as e:
            # Generic exception handler for any other unforeseen issues
            logger.error(f"An unexpected error occurred: {e}")
            all_content = ''
        
        if not all_content.strip():
            return HttpResponse("No content found", status=404)

        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_content)

        # Save to a bytes buffer
        buffer = io.BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.savefig(buffer, format='png')
        buffer.seek(0)
            # Return the image as an HTTP response
        return HttpResponse(buffer, content_type='image/png')


@login_required
def home(request):
    """
    Home view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Home page.
    """
    if not service_available(solr_core_ping_url):
        return render(request, 'earkweb/error.html', {'header': 'SolR server unavailable', 'message': "Required service is not available at: %s" % solr_core_ping_url})
    template = loader.get_template('earkweb/home.html')

    mime_type_stats = get_mime_type_counts()

    file_size_data = get_file_size_per_mime_type()


    context = {
        'sw_version': sw_version,
        'sw_version_date': sw_version_date,
        'labels': mime_type_stats['labels'], # ["a", "b", "c"],
        'data': mime_type_stats['data'], # [20, 60, 20],
        'file_size_data': file_size_data  # Pass the entire dictionary
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def version(request):
    """
    Version view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Version page.
    """
    template = loader.get_template('earkweb/version.html')
    context = {

    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def check_folder_exists(_, folder):
    """
    Check if a specified folder exists in the configured path.

    This view constructs the full path to the folder by joining the 
    configured working directory (`config_path_work`) with the provided 
    folder name and checks if this path exists on the filesystem.

    Parameters:
    - request: The HTTP request object.
    - folder: The name of the folder to check for existence.

    Returns:
    - HttpResponse: A response with a string 'true' or 'false' indicating whether
      the folder exists.

    Decorators:
    - @login_required: Ensures the view can only be accessed by authenticated users.
    - @csrf_exempt: Exempts the view from CSRF verification (use with caution).

    Example:
    - If `config_path_work` is '/path/to/work' and `folder` is 'test_folder', the 
      function will check if '/path/to/work/test_folder' exists.
    """
    path = os.path.join(config_path_work, folder)
    return HttpResponse(str(os.path.exists(path)).lower())


@login_required
@csrf_exempt
def check_identifier_exists(_, identifier):
    """
    Check if an InformationPackage with the specified identifier exists.

    This view is protected by login and CSRF exemption decorators. It queries the
    InformationPackage model to check if an object with the given identifier exists.

    Parameters:
    - request: The HTTP request object.
    - identifier: The unique identifier of the InformationPackage to check.

    Returns:
    - HttpResponse: A response with a string 'true' if the identifier exists, 'false' otherwise.

    Decorators:
    - @login_required: Ensures the view can only be accessed by authenticated users.
    - @csrf_exempt: Exempts the view from CSRF verification (use with caution).

    Example:
    - If an InformationPackage with identifier '12345' exists, the function will return 'true'.
      Otherwise, it will return 'false'.
    """
    try:
        # pylint: disable-next=no-member
        InformationPackage.objects.get(identifier=identifier)
        return HttpResponse("true")
    except ObjectDoesNotExist:
        return HttpResponse("false")


@login_required
@csrf_exempt
def check_submission_exists(request, package_name):
    """
    Check if a submission exists for a given package name.

    This view function checks if an `InformationPackage` with the given `package_name`
    exists in the database and if the corresponding file exists in the configured path.

    Args:
        request (HttpRequest): The HTTP request object.
        package_name (str): The name of the package to check.

    Returns:
        HttpResponse: A response with a string "true" or "false" indicating whether the
                      submission exists.
    """
    try:
        # pylint: disable-next=no-member
        ip = InformationPackage.objects.get(package_name=package_name)
        exists = ip and os.path.exists(os.path.join(config_path_work, ip.uid))
        return HttpResponse(str(exists).lower())
    except ObjectDoesNotExist:
        return HttpResponse("false")


def working_area2(request, section, uid):
    """
    Render the working area page for information package management, submission, or access.

    This function determines the type of operation (management, submission, or access)
    based on the request path, sets the appropriate title and section, and fetches the
    directory JSON data from an API endpoint. It then renders the 'workingarea2.html'
    template with the fetched data and additional context.

    Args:
        request (HttpRequest): The HTTP request object.
        section (str): The section of the working area ('management', 'submission', or 'access').
        uid (str): The unique identifier for the information package.

    Returns:
        HttpResponse: The rendered HTML response for the working area page.
    """
    template = loader.get_template('earkweb/workingarea2.html')
    request.session['uid'] = uid
    r = request.META['PATH_INFO']
    title = trans("Information package management") if "management" in r else trans("Submission") if "submission" in r else trans("Access")
    section = "management" if "management" in r else "submission" if "submission" in r else "access"
    schema, domain = get_domain_scheme(request.headers.get("Referer"))
    url = "%s://%s/earkweb/api/ips/%s/dir-json" % (schema, domain, uid)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    context = {
        "title": title,
        "section": section,
        "uid": uid,
        "dirasjson": response.content.decode('utf-8'),
        "django_backend_service_api_url": django_backend_service_api_url
    }
    return HttpResponse(template.render(context=context, request=request))


def get_domain_scheme_from_request(request):
    url = request.build_absolute_uri()
    parsed_url = urlparse(url)
    return parsed_url.scheme, parsed_url.netloc


@login_required
def storage_area(request, section, identifier):
    """
    Handles the display and management of storage areas for information packages.

    This view is responsible for rendering a page that displays the directory
    structure and version timeline of a specific information package identified
    by `identifier`. The title and section of the page are determined based on
    the HTTP referer.

    Args:
        request (HttpRequest): The HTTP request object.
        section (str): The section of the storage area (e.g., management, submission, access).
        identifier (str): The unique identifier of the information package.

    Returns:
        HttpResponse: The HTTP response with the rendered template.
    """
    template = loader.get_template('earkweb/workingarea2.html')
    request.session['identifier'] = identifier
    if "HTTP_REFERER" in request.META:
        r = request.META['HTTP_REFERER']
        title = "Information package management" if "management" in r else "Submission" if "submission" in r else "Access"
        section = "management" if "management" in r else "submission" if "submission" in r else "access"
    else:
        title = "Access"
        section = section if section else "access"
    #store_path = "%s" % make_storage_data_directory_path(identifier, config_path_storage)
    #logger.info(store_path)
    #schema, domain = get_domain_scheme(request.headers.get("Referer"))
    schema, domain = get_domain_scheme_from_request(request)
    url = f"{schema}://{domain}/earkweb/api/storage/ips/{identifier}/dir-json"
    user_api_token = get_user_api_token(request.user)
    response = requests.get(
        url, 
        headers={'Authorization': f'Token {user_api_token}'}, 
        verify=verify_certificate,
        timeout=10
    )
    if response.status_code != 200:
        return render(request, 'earkweb/error.html', {
            'header': 'Archived object does not exist (%d)' % response.status_code,
            'details': response.text
        })

    inventory_url = f"{schema}://{domain}/earkweb/api/ips/{identifier}/file-resource/inventory.json"
    inventory_response = requests.get(
        inventory_url, 
        headers={'Authorization': f'Token {user_api_token}'}, 
        verify=verify_certificate,
        timeout=10
    )
    inventory = json.loads(inventory_response.text)
    try:
        version_timeline_data = [
            {
                "id": re.sub(r"\D", "", key),
                "content": f"{val['message']} ({key})",
                "start": val["created"],
                "className": "myClassName",
            }
            for key, val in inventory.get("versions", {}).items()
        ]
    except KeyError as e:
        error_details = f"Missing key in inventory data: {e}"
        return render(request, 'earkweb/error.html', {
            'header': 'Version information not available in inventory',
            'details': error_details
        })
    except TypeError as e:
        error_details = f"Invalid type encountered: {e}"
        return render(request, 'earkweb/error.html', {
            'header': 'Version information not available in inventory',
            'details': error_details
        })
    except Exception as e:
        # Generic catch-all for other unexpected exceptions
        error_details = f"An unexpected error occurred: {e}"
        return render(request, 'earkweb/error.html', {
            'header': 'Invalid inventory',
            'details': error_details
        })

    times = [val["created"] for key, val in inventory["versions"].items()]
    times.sort()
    if len(times) > 1:
        min_dtstr = times[0]
        max_dtstr = times[len(times)-1]
        min_dt = get_date_from_iso_str(min_dtstr, DT_ISO_FORMAT)
        max_dt = get_date_from_iso_str(max_dtstr, DT_ISO_FORMAT)
        delta =  max_dt - min_dt
        scale = ("seconds", (delta.seconds)) if delta.seconds < 60 \
            else ("minutes", int(delta.seconds/60)) if delta.seconds < 3600 \
            else ("hours", int(delta.seconds/3600)) if delta.seconds < 86400 \
            else ("days", (delta.days)) if delta.seconds < 2592000 \
            else ("months", int(delta.days/30)) if delta.seconds < 31536000 \
            else ("years", int(delta.days/365))
        scale_unit, scale_value = scale
    else:
        min_dtstr = max_dtstr = times[0]
        scale_unit = "days"
        scale_value = "3"

    context = {
        "title": title,
        "section": section,
        "uid": identifier,
        "dirasjson": response.content.decode('utf-8'),
        "show_timeline": True,
        "identifier": identifier,
        "version_timeline_data": version_timeline_data,
        "scale_unit": scale_unit,
        "scale_value": (scale_value*10),
        "min_dt": min_dtstr,
        "max_dt": max_dtstr
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def read_file(request, ip_sub_file_path, area=None):
    """
    Read file from a defined area using the information package sub file path

    Args:
        request: Request
        ip_sub_file_path: path to be read from working directory

    Returns:
        HttpResponse: The HTTP response with the rendered template.
    """
    parts = ip_sub_file_path.split("/")
    uid = parts[0]
    path = ip_sub_file_path.lstrip(parts[0]).lstrip("/")
    area = area if area else "ips"
    schema, domain = get_domain_scheme(request.headers.get("Referer"))
    uid = from_safe_filename(uid)
    url = "%s://%s/earkweb/api/%s/%s/file-resource/%s/" % (schema, domain, area, uid, path)
    user_api_token = get_user_api_token(request.user)
    api_response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    content_type = api_response.headers['content-type']
    response = HttpResponse(api_response.content, content_type=content_type)
    if "Content-Disposition" in api_response.headers:
        response['Content-Disposition'] = api_response.headers['Content-Disposition']
    return response


@login_required
@csrf_exempt
def get_directory_json(request):
    """
    Handles a POST request to retrieve a JSON representation of a directory structure.

    This view requires the user to be logged in and exempts the request from CSRF verification.
    It expects a POST request with a 'uid' parameter, which is used to locate a specific directory.

    Args:
        request (HttpRequest): The HTTP request object, expected to contain a 'uid' parameter in POST data.

    Returns:
        JsonResponse: A JSON response containing the directory structure rooted at the specified user's directory.
                      The response also includes a check_callback flag set to "true".

    Raises:
        KeyError: If 'uid' is not provided in the POST data.
        FileNotFoundError: If the directory specified by 'uid' does not exist.

    """
    uid = request.POST['uid']
    work_dir = os.path.join(config_path_work, uid)
    dirlist = os.listdir(work_dir)
    if len(dirlist) > 0:
        package_name = dirlist[0]
    else:
        package_name = dirlist
    return JsonResponse({ "data": path_to_dict(work_dir, strip_path_part=config_path_work+'/'), "check_callback": "true"})


@login_required
@csrf_exempt
def get_storage_directory_json(request):
    """
    Handles a POST request to retrieve the storage directory contents as JSON.

    This view is protected by login and CSRF exempt. It processes an identifier from the 
    request to determine the corresponding storage directory, lists its contents, and 
    returns a JSON response with the directory structure.

    Args:
        request (HttpRequest): The HTTP request object containing a POST parameter 'identifier'.

    Returns:
        JsonResponse: A JSON response containing the directory structure and a callback check.

    Raises:
        KeyError: If 'identifier' is not found in the POST data.
    """
    identifier = request.POST['identifier']
    storage_dir = make_storage_data_directory_path(identifier, config_path_storage)
    dirlist = os.listdir(storage_dir)
    if len(dirlist) > 0:
        package_name = dirlist[0]
    else:
        package_name = dirlist
    return JsonResponse({"data": path_to_dict(storage_dir, strip_path_part=config_path_storage+'/'), "check_callback": "true"})


@login_required
@csrf_exempt
def poll_state(request):
    """
    Handles an AJAX POST request to poll the state of an asynchronous task.

    This view is protected by login and is exempt from CSRF protection. It checks the 
    state of a task using its ID and returns the state along with any result or info.

    Args:
        request (django.core.handlers.wsgi.WSGIRequest): The HTTP request object containing 
        the POST parameter 'task_id'.

    Returns:
        django.http.JsonResponse: A JSON response containing the task state metadata.
        - If successful, includes 'success': True, 'state', and either 'result' or 'info'.
        - If unsuccessful, includes 'success': False and 'errmsg' with an error message.

    Raises:
        Exception: Captures any exception, logs the traceback, and includes the error message 
        in the JSON response.
    """
    data = {"success": False, "errmsg": "undefined"}
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                if task.state == "SUCCESS":
                    data = {"success": True, "state": task.state, "result": task.result}
                else:
                    data = {"success": True, "state": task.state, "info": task.info}
            else:
                data = {"success": False, "errmsg": "No task_id in the request"}
        else:
            data = {"success": False, "errmsg": "Not ajax"}
    except KeyError:
        data = {
            "success": False,
            "errmsg": "KeyError: Required key is missing in the request"
        }
    except Exception as err:
        data = {
            "success": False,
            "errmsg": f"An error occurred: {str(err)}"
        }
        tb = traceback.format_exc()
        logging.error(tb)
    return JsonResponse(data)


@login_required
@csrf_exempt
def solrif(request, core, operation):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.
    - core: the Solr core
    - operation: operation touse 

    Returns:
    - HttpResponse: JSON response
    """
    logger.debug("SolR query")
    logger.debug("Core: %s", core)
    logger.debug("Operation: %s", operation)
    logger.debug("Query: %s",  request.GET.get('q', ''))
    start = request.GET.get('start', '0')
    logger.debug("Start: %s",  start)
    sort = request.GET.get('sort', '')
    logger.debug("Sort: %s",  sort)
    rows = request.GET.get('rows', '20')
    logger.debug("Rows: %s",  rows)
    field_list = request.GET.get('fl', '')
    logger.debug("Field list: %s",  field_list)
    q = urlencode({
        'q': request.GET.get('q', ''),
        "fl": field_list,
        "sort": sort,
        "start": start,
        "rows": rows,
        "wt": "json",
        "json.wrf": "callback"
    })
    query_url = f"http://{solr_host}:{solr_port}/solr/{solr_core}/{operation}?{q}"
    logger.debug(query_url)
    data = ""
    try:
        response = requests.get(
            query_url,
            verify=verify_certificate,
            timeout=10
        )
        return HttpResponse(
            response.text,
            content_type='application/javascript; charset=utf-8'
        )
    except requests.exceptions.Timeout:
        logger.error("Request timed out.")
        return HttpResponse(
            "The request timed out. Please try again later.",
            content_type='text/plain'
        )
    except requests.exceptions.ConnectionError:
        logger.error("Connection error occurred.")
        return HttpResponse(
            "A connection error occurred. Please check your network connection.",
            content_type='text/plain'
        )
    except requests.exceptions.RequestException as err:
        tb = traceback.format_exc()
        logger.error("An error occurred: %s", err)
        logger.error(tb)
        return HttpResponse(
            "An error occurred while processing the request.",
            content_type='text/plain'
        )
    return data


@login_required
@csrf_exempt
def howto_create_dataset(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/create_dataset.html')
    return HttpResponse(template.render(context={}, request=request))

@login_required
@csrf_exempt
def howto_ingest_dataset(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/ingest_dataset.html')
    return HttpResponse(template.render(context={}, request=request))

@login_required
@csrf_exempt
def howto_overview(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/howto_overview.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
@csrf_exempt
def howto_annotate_manually(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/annotate_manually.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
@csrf_exempt
def howto_batch_annotate(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/batch_annotate.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
@csrf_exempt
def howto_apply_predefined_labels(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/apply_predefined_labels.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
@csrf_exempt
def howto_persist_annotations(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/persist_annotations.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
@csrf_exempt
def howto_add_new_vocabulary(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/add_new_vocabulary.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
@csrf_exempt
def howto_use_the_api(request):
    """
    Howto page view

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Howto page.
    """
    template = loader.get_template('earkweb/howto/use_the_api.html')
    return HttpResponse(template.render(context={}, request=request))


@login_required
def oai_pmh(request):
    """
    OAI-PMH Overview

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: OAI-PMH Overview Page
    """
    # Fetch the first InformationPackage with a non-empty identifier
    ip = InformationPackage.objects.filter(identifier__isnull=False).exclude(identifier="").first()

    # Render the template with the context
    return render(request, 'earkweb/oai_pmh.html', {"identifier": ip.identifier if ip else None})


@login_required
def resource_sync(request):
    """
    ResourceSync Overview

    Parameters:
    - request: The HTTP request object.

    Returns:
    - HttpResponse: Resource Sync Overview Page
    """
    # Fetch the first InformationPackage with a defined identifier
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.filter(identifier__isnull=False).first()

    # Render the template with the context
    template = loader.get_template('earkweb/resourcesync.html')
    return HttpResponse(template.render(context={"identifier": ip.identifier if ip else None}, request=request))