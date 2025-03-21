import datetime
import json
from math import e
import os
import shutil
import string
import traceback
import logging
import uuid
from itertools import chain
import django_tables2 as tables
import pycountry
import requests
import simplejson
import tempfile
import mimetypes
from urllib.parse import quote
from requests.auth import HTTPBasicAuth
from rdflib import Literal
from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.http import HttpResponse
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig
from earkweb.views import get_domain_scheme
from eatb.utils.datetime import DT_ISO_FORMAT_FILENAME, DT_ISO_FORMAT, ts_date, DATE_DMY, date_format
from eatb.utils.dictutils import dict_keys_underscore_to_camel, dict_keys_camel_to_underscore
from eatb.utils.randomutils import get_unique_id
from eatb.utils.fileutils import get_immediate_subdirectories, find_files
from eatb.utils.fileutils import encode_identifier, decode_identifier
from eatb.utils.stringutils import safe_path_string
from eatb.checksum import ChecksumFile, ChecksumAlgorithm
from config.configuration import flower_user
from config.configuration import flower_password
from config.configuration import documentation_directory, representations_directory, \
    flower_service_url, node_namespace_id, \
    package_access_url_pattern, repo_id, repo_title, repo_description, repo_catalogue_issued, \
    repo_catalogue_modified, \
    verify_certificate, django_backend_service_api_url, metadata_directory, django_backend_service_url, \
    django_service_url, accepted_identifier_examples, config_max_http_download
from eatb.utils.fileutils import to_safe_filename
from config.configuration import config_path_work, config_path_reception
from config.configuration import identifier_pattern
from config.configuration import urn_event_pattern
from earkweb.models import InformationPackage
from earkweb.models import Representation, InternalIdentifier, Vocabulary
from earkweb.utils.representation_utils import register_representations_from_data_package
from util.djangoutils import get_unused_identifier, get_user_api_token
from taskbackend.taskexecution import execute_task
from taskbackend.taskutils import extract_and_remove_package, \
    get_celery_worker_status, flower_is_running, get_task_info_from_child_tasks
from taskbackend.tasks import initialize_package_from_reception

from submission.forms import MetaFormStep1, MetaFormStep2, TinyUploadFileForm, \
    MetaFormStep4, MetaFormStep3, MetaFormStep5


from django.utils.translation import gettext_lazy as _

from util.flowerapiclient import get_task_info, get_task_list

import unicodedata
from mutagen import File as MutagenFile
from moviepy import VideoFileClip

logger = logging.getLogger(__name__)


def normalize_filename(filename):
    return unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('utf-8')


@login_required
@csrf_exempt
def ip_detail_table(request):
    pkg_id = request.POST['pkg_id']
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pkg_id)
    context = {
        "ip": ip,
        "config_path_work": config_path_work
    }
    return render(request, 'submission/iptable.html', context=context)


@login_required
def start(request):
    template = loader.get_template('submission/start.html')
    # pylint: disable-next=no-member
    int_ids = InternalIdentifier.objects.filter(user=request.user.id, used=0)
    int_ids_values = int_ids.values()
    num_blockchain_ids = len([i for i in int_ids_values if i['is_blockchain_id'] == 1])
    num_selfgen_ids = len([i for i in int_ids_values if i['is_blockchain_id'] == 0])
    # Parse into a list of dictionaries
    accepted_identifier_examples_list = [
        {"type": field.split(': ')[0].strip(), "value": field.split(': ')[1].strip()}
        for field in accepted_identifier_examples.split(',')
    ]
    context = {
        'num_int_ids': len(int_ids),
        'num_blockchain_ids': num_blockchain_ids,
        'num_selfgen_ids': num_selfgen_ids,
        'identifier_pattern': identifier_pattern,
        'accepted_identifier_examples_list': accepted_identifier_examples_list
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def fileresource(request, item, ip_sub_file_path):
    user_api_token = get_user_api_token(request.user)
    schema, domain = get_domain_scheme(request.headers.get("Referer"))
    url = "%s://%s/earkweb/api/ips/%s/file-resource/%s/" % (
        schema, domain, item, ip_sub_file_path)
    if request.method == "GET":
        response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
        content_type = response.headers['content-type']
        return HttpResponse(response.content, content_type=content_type)
    elif request.method == "POST":
        # POST is translated to delete (kv-file-explorer triggers post request for delete action)
        response = requests.delete(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
        return JsonResponse({'success': True}, status=response.status_code)


@login_required
@csrf_exempt
def receptionresource(request, ip_sub_file_path):
    user_api_token = get_user_api_token(request.user)
    schema, domain = get_domain_scheme(request.headers.get("Referer"))
    url = f"{schema}://{domain}/earkweb/api/reception/file-resource/{ip_sub_file_path}/"
    if request.method == "GET":
        response = requests.get(
            url, 
            headers={'Authorization': f'Token {user_api_token}'}, 
            verify=verify_certificate, 
            timeout=10
        )
        content_type = response.headers['content-type']
        return HttpResponse(response.content, content_type=content_type)
    elif request.method == "POST":
        # POST is translated to delete (kv-file-explorer triggers post request for delete action)
        response = requests.delete(
            url, 
            headers={'Authorization': f'Token {user_api_token}'}, 
            verify=verify_certificate, 
            timeout=10
        )
        return JsonResponse({'success': True}, status=response.status_code)


@login_required
@csrf_exempt
def upload(request):
    if request.method == "POST":
        posted_files = request.FILES
        if 'file_data' not in posted_files:
            return JsonResponse({'error': "No files available"}, status=500)
        else:
            # distribution metadata
            rep = request.POST["rep"]
            # get information package
            # pylint: disable-next=no-member
            ip = InformationPackage.objects.get(uid=request.POST["uid"])
            try:
                # pylint: disable-next=no-member
                reprec = Representation.objects.get(ip=ip, identifier=rep)
            except ObjectDoesNotExist:
                # pylint: disable-next=no-member
                reprec = Representation.objects.create(ip=ip, identifier=rep)
            reprec.accessRights = request.POST["access_rights"]
            reprec.description = request.POST["distribution_description"]
            reprec.license = request.POST["offer"]
            reprec.save()
            rep_info = {
                        'access_rights': request.POST['access_rights'],
                        'distribution_description': request.POST['distribution_description'],
                    }
            reps_in_session = None
            if 'representations' in request.session:
                reps_in_session = request.session['representations']
            if reps_in_session and isinstance(reps_in_session, dict):
                reps_in_session[rep] = rep_info
            else:
                reps_in_session = {rep: rep_info}
            request.session['representations'] = reps_in_session

            # pylint: disable-next=no-member
            ip = InformationPackage.objects.get(uid=request.POST['uid'])
            u = User.objects.get(username=request.user)
            # if u != ip.user:
            #    return JsonResponse({'error': "Unauthorized. Operation is not permitted."}, status=500)
            ip_work_dir = os.path.join(config_path_work, request.POST['uid'])
            data_path = os.path.join(ip_work_dir, representations_directory, request.POST['rep'], "data")
            os.makedirs(data_path, exist_ok=True)
            file_data = posted_files['file_data']
            filename = file_data.name
            file_path = os.path.join(data_path, filename)

            with open(file_path, 'wb+') as destination:
                for chunk in posted_files['file_data'].chunks():
                    destination.write(chunk)

            file_upload_resp = {
                "ver": "1.0",
                "ret": True,
                "errcode": 0,
                "data": {
                    "status": "upload success",
                    "originalFilename": filename,
                    "fileName": filename,
                    "fileType": "image/jpg",
                    "fileSize": 255997
                }

            }
            return JsonResponse(file_upload_resp, status=201)
    else:
        template = loader.get_template('submission/upload.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


def reception_task_status(request, task_id):
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
    

@login_required
@csrf_exempt
def ip_upload(request):
    """Upload files to information package"""
    if request.method == "POST":
        posted_files = request.FILES
        if 'file_data' not in posted_files:
            return JsonResponse({'error': "No files available"}, status=500)
        else:
            # get information package
            # pylint: disable-next=no-member
            ip = InformationPackage.objects.get(uid=request.POST["uid"])
            # pylint: disable-next=unused-variable
            u = User.objects.get(username=request.user)
            # if u != ip.user:
            #    return JsonResponse({'error': "Unauthorized. Operation is not permitted."}, status=500)
            ip_work_dir = os.path.join(config_path_work, ip.uid)

            file_data = posted_files['file_data']
            filename = file_data.name
            sanitized_filename = normalize_filename(filename)
            target_directory = os.path.join(ip_work_dir, "documentation")
            file_path = os.path.join(ip_work_dir, "documentation", sanitized_filename)
            if not os.path.exists(target_directory):
                os.makedirs(target_directory, exist_ok=True)

            with open(file_path, 'wb+') as destination:
                for chunk in posted_files['file_data'].chunks():
                    destination.write(chunk)

            file_upload_resp = {
                "ver": "1.0",
                "ret": True,
                "errcode": 0,
                "data": {
                    "status": "upload success",
                    "originalFilename": filename,
                    "fileName": filename,
                    "fileType": "image/jpg",
                    "fileSize": 255997
                }

            }
            return JsonResponse(file_upload_resp, status=201)
    else:
        template = loader.get_template('submission/upload.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def upload_packaged_sip(request):
    """Upload files to information package"""
    if request.method == "POST":
        posted_files = request.FILES
        if 'file_data' not in posted_files:
            return JsonResponse({'error': "No files available"}, status=500)
        else:

            file_data = posted_files['file_data']
            filename = file_data.name
            file_path = os.path.join(config_path_reception, filename)

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"

            if not filename.endswith(('.tar', '.tar.gz', '.zip')):
                file_upload_resp = {
                    "ver": "1.0",
                    "ret": True,
                    "errcode": 1,
                    "data": {
                        "status": "Unsupported file extension. Please upload a .tar, .tar.gz, or .zip file.",
                        "originalFilename": filename,
                        "fileName": filename,
                        "mimeType": mime_type,
                        "fileSize": file_data.size,
                    }
                }
                return JsonResponse(file_upload_resp, status=415) # HTTP 415: Media type not supported

            with open(file_path, 'wb+') as destination:
                for chunk in posted_files['file_data'].chunks():
                    destination.write(chunk)

            if os.path.exists(file_path):
                logger.info(f"Temporary fle created at: {file_path}")       
            else:
                raise FileNotFoundError(f"File not created at: {file_path}")   
            
            # pylint: disable-next=no-member
            uid = get_unique_id()
            # extract the package name from a file with extensions like .zip, .tar, or .tar.gz
            package_name = '.'.join(filename.split('.')[:-2]) if filename.endswith(('.tar.gz')) else '.'.join(filename.split('.')[:-1])
            # pylint: disable-next=no-member
            InformationPackage.objects.create(
                work_dir=os.path.join(config_path_work, uid), uid=uid,
                package_name=package_name, external_id="", user=request.user, version=0
            )
            
            # pylint: disable-next=no-member
            ip = InformationPackage.objects.get(uid=uid)

            representations = register_representations_from_data_package(file_path, ip)

            job = initialize_package_from_reception.delay(
                container_path=file_path,
                uid=uid,
                representations=representations
            )
            
            sha256 = ChecksumFile(file_path).get(ChecksumAlgorithm.SHA256)
            file_upload_resp = {
                "ver": "1.0",
                "ret": True,
                "errcode": 0,
                "data": {
                    "status": "File upload successful",
                    "originalFilename": filename,
                    "fileName": filename,
                    "mimeType": mime_type,
                    "fileSize": file_data.size,
                    "sha256Hash": sha256,
                    "uid": uid,
                    "jobid": job.id
                }

            }
            return JsonResponse(file_upload_resp, status=201)
    else:
        template = loader.get_template('submission/upload_data_packages.html')
    context = {
        "max_upload_file_size": config_max_http_download,
        "flower_service_url": flower_service_url,
        "django_service_url": django_service_url,        
    }
    return HttpResponse(template.render(context=context, request=request))


def upload_step1(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    if "package_name" in request.POST and request.POST["package_name"] != ip.package_name:
        ip.package_name = request.POST["package_name"]
        ip.save()
    if "external_id" in request.POST and request.POST["external_id"] != ip.external_id:
        ip.external_id = encode_identifier(request.POST["external_id"])
        ip.save()
    user_api_token = get_user_api_token(request.user)
    dir_info_request_url = "%s/ips/%s/dir-json" % (django_backend_service_api_url, ip.uid)
    dir_info_resp = requests.get(dir_info_request_url,
                                 headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    if dir_info_resp.status_code == 200:
        dir_data = json.loads(dir_info_resp.text)
        if dir_data and "data" in dir_data and "children" in dir_data['data']:
            dirs = dir_data['data']['children']
            folder_list = [entry['children'] for entry in dirs if entry['text'] == 'representations']
            if len(folder_list) > 0:
                folders = folder_list[0]
                folder_names = [folder['text'] for folder in folders]
                for fn in folder_names:
                    # pylint: disable-next=no-member
                    obj, created = Representation.objects.get_or_create(identifier=fn, ip=ip)
                    if created:
                        obj.save()

    if request.method == 'POST':
        realtags = []
        usertags = []
        form = MetaFormStep1(request.POST)
        post_data = request.POST
        if "package_name" in post_data and post_data["package_name"] != ip.package_name:
            ip.package_name = post_data["package_name"]
            ip.save()
        # distinguish between tags and user generated tags
        if 'hidden_user_tags' in post_data:
            splittags = None
            try:
                splittags = simplejson.loads(post_data['hidden_user_tags'])
            except simplejson.errors.JSONDecodeError:
                if isinstance(post_data['hidden_user_tags'], str):
                    splittags = [{'custom': True, 'value': x.strip()} for x in post_data['hidden_user_tags'].split(',')]
            if "tags" in post_data:
                usertags = post_data["tags"].split(',')
            if splittags:
                for splittag in splittags:
                    if splittag['custom']:
                        usertags.append(splittag['value'])
                    else:
                        realtags.append(splittag['value'])
            if realtags:
                for t in realtags:
                    ip.tags.add(t)
                ip.save()
        data3 = dict(post_data.items())
        data3['tags'] = realtags
        data3['user_generated_tags'] = usertags

        # remove query parameter
        data3.pop("q", None)
        data3.pop("selected_items", None)
        data3.pop("selected_data", None)

        data4 = {key: Literal(val) if isinstance(val, list) else Literal(val) for key, val in data3.items()}

        # Linked data items
        selected_items = request.POST.getlist("selected_items") 
        parsed_items = [] 
        for item in selected_items:
            if "|" in item:  
                link,label = item.split("|", 1)  
                parsed_items.append({"label": label.strip(), "link": link.strip()}) 
        data4['linked_data'] = parsed_items


        if form.is_valid():
            request.session['step1'] = data4
            url = "/earkweb/submission/upload_step2/%s/" % (str(ip.id))
            return HttpResponseRedirect(url)
        else:
            errors = ['error1']
            return render(request, 'submission/upload_mdform.html', {'form': form, 'errors': errors})
    else:
        # unset metadata properties in case they exist
        if 'md_properties' in request.session:
            del request.session['md_properties']
        if 'distr_properties' in request.session:
            del request.session['distr_properties']
        if 'rep' in request.session:
            del request.session['rep']
        # try to read existing metadata file
        tags = []
        user_generated_tags = []
        # if the file is available, parse it and get metadata properties
        selected_items_data = [] 
        if ip.basic_metadata and ip.basic_metadata != 'null':
            md_properties = json.loads(ip.basic_metadata)

            md_properties = dict_keys_camel_to_underscore(md_properties)

            # Extract linked data if available
            if "linked_data" in md_properties and isinstance(md_properties["linked_data"], list):
                selected_items_data = md_properties["linked_data"]  

            request.session['md_properties'] = md_properties
            # load existing metadata values as initial form values
            form = MetaFormStep1(initial={
                'package_name': ip.package_name,
                'external_id': ip.external_id,
                'title': md_properties["title"],
                'description': md_properties["description"],
                'locations': md_properties["locations"] if "locations" in request.session['md_properties'] else "{}",
                'original_creation_date': md_properties["original_creation_date"] if "original_creation_date" in request.session['md_properties'] else "",
                'content_information_type': md_properties["content_information_type"] if "content_information_type" in request.session['md_properties'] else "MIXED",
                'content_category': md_properties["content_category"] if "content_category" in request.session['md_properties'] else "Mixed"
            })
        else:
            form = MetaFormStep1(initial={
                'package_name': ip.package_name,
                'external_id': ip.external_id,
            })
        return render(request, 'submission/upload_mdform.html', {
            'form': form,
            'ip': ip,
            'selected_items_data': selected_items_data,
            'tags': [val.name for val in ip.tags.all()],
            'user_generated_tags': user_generated_tags,
            'locations': request.session['md_properties']["locations"] if "md_properties" in request.session.keys() and "locations" in request.session['md_properties'] else {}
        })


def upload_step2(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    loc_strs = "[]"
    if request.method == 'POST':

        form = MetaFormStep2(request.POST)
        data2 = request.POST
        data3 = dict(data2.items())
        data4 = {key: Literal(val[0]) if isinstance(val, list) else Literal(val) for key, val in data3.items()}
        if form.is_valid():
            request.session['step2'] = data4
            url = "/earkweb/submission/upload_step3/%s/" % (str(pk))
            return HttpResponseRedirect(url)
        else:
            errors = ['error1']
            return render(request, 'submission/upload_mdform.html', {'form': form, 'errors': errors})
    else:
        if 'md_properties' in request.session:
            md_properties = request.session['md_properties']
            loc_strs = request.session['md_properties']["locations"] if "md_properties" in request.session.keys() and "locations" in request.session['md_properties'] else '[]'
            form = MetaFormStep2(initial={
                'locations': loc_strs
            })
        else:
            form = MetaFormStep2()
    #locs['locations'] = loc_list
    if isinstance(loc_strs, str):
        try:
            # If it's a string
            json_dict = json.dumps(json.loads(loc_strs))
        except json.JSONDecodeError:
            json_dict = json.dumps([])  # Fallback
    elif isinstance(loc_strs, (list, dict)):
        # If it's already a python object
        json_dict = json.dumps(loc_strs)
    else:
        json_dict = json.dumps([])  # Fallback
    return render(request, 'submission/upload_mdform.html', {'form': form, 'ip': ip, 'locations': json_dict})


def upload_step3(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)

    if request.method == 'POST':

        form = MetaFormStep3(request.POST)
        data2 = request.POST
        data3 = dict(data2.items())
        data4 = {key: Literal(val[0]) if isinstance(val, list) else Literal(val) for key, val in data3.items()}
        if form.is_valid():
            request.session['step3'] = data4
            url = "/earkweb/submission/upload_step4/%s/" % (str(pk))
            return HttpResponseRedirect(url)
        else:
            errors = ['error1']
            return render(request, 'submission/upload_mdform.html', {'form': form, 'errors': errors})
    else:
        if 'md_properties' in request.session:
            md_properties = request.session['md_properties']
            contact_point = md_properties["contact_point"] if "contact_point" in md_properties else ""
            contact_email = md_properties["contact_email"] if "contact_email" in md_properties else ""
            publisher = md_properties["publisher"] if "publisher" in md_properties else ""
            publisher_email = md_properties["publisher_email"] if "publisher_email" in md_properties else ""
            language = md_properties["language"] if "language" in md_properties else ""
            form = MetaFormStep3(initial={
                'contact_point': contact_point,
                'contact_email': contact_email,
                'publisher': publisher,
                'publisher_email': publisher_email,
                'language': language,

            })
        else:
            form = MetaFormStep3()
    return render(request, 'submission/upload_mdform.html', {'form': form, 'ip': ip})


def upload_step4(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)

    if request.method == 'POST':

        form = MetaFormStep4(request.POST)
        data2 = request.POST
        data3 = dict(data2.items())
        data4 = {key: Literal(val[0]) if isinstance(val, list) else Literal(val) for key, val in data3.items()}
        if form.is_valid():
            request.session['step4'] = data4
            url = "/earkweb/submission/upload_step5/%s/" % (str(pk))
            return HttpResponseRedirect(url)
        else:
            errors = ['error1']
            return render(request, 'submission/upload_mdform.html', {'form': form, 'errors': errors})
    else:
        if 'md_properties' in request.session:
            md_properties = request.session['md_properties']
            documentation_description = md_properties["documentation_description"] if "documentation_description" in md_properties else ""

            form = MetaFormStep4(initial={
                'documentation_description': documentation_description
            })
        else:
            form = MetaFormStep4()
    return render(request, 'submission/upload_mdform.html', {'form': form, 'ip': ip, 'django_backend_service_url': django_backend_service_url})


@login_required
def upload_step5(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)

    template = loader.get_template('submission/upload_distributions.html')
    upload_file_form = TinyUploadFileForm()

    # pylint: disable-next=no-member
    reprs_qs = Representation.objects.filter(ip=ip).order_by('id')

    # get representation from session or first reprsentation otherwise
    # if there is no representation, assign an unused identifier
    if "rep" in request.session:
        repname = request.session["rep"]
    elif reprs_qs:
        repname = reprs_qs[0].identifier
    else:
        representations_path = os.path.join(config_path_work, ip.uid, representations_directory)
        representation_dirs = get_immediate_subdirectories(representations_path)
        if representation_dirs:
            repname = representation_dirs[0]
            try:
                # pylint: disable-next=no-member
                Representation.objects.get(ip=ip, identifier=repname)
            except ObjectDoesNotExist:
                # pylint: disable-next=no-member
                Representation.objects.create(ip=ip, identifier=repname)
        else:
            repname = get_unused_identifier(request.user.id)

    # pylint: disable-next=no-member
    reprs_qs = Representation.objects.filter(ip=ip).order_by('id')

    repr_dir_names = None
    reprs = {}
    if repname:
        reprs = {
            r['identifier']: {
                **r,
                'file_metadata': {} if r['file_metadata'] is None else r['file_metadata']
            }
            for r in list(
                reprs_qs.values(
                    "id", "identifier", "label", "description", "license", "accessRights", "file_metadata"
                )
            )
        }
        repr_dir_names = list(reprs_qs.values_list('identifier', flat=True))
        if repname in reprs:
            curr_repr = reprs[repname]
            form = MetaFormStep5(initial={
                    'distribution_description': curr_repr['description'],
                    'distribution_label': curr_repr['label'],
                    'access_rights': curr_repr['accessRights'],
                    'file_metadata': curr_repr['file_metadata']
                })
        else:
            form = MetaFormStep5(request.POST)
    else:
        form = MetaFormStep5(request.POST)

    context = {
        'uid': ip.uid,
        'django_backend_service_api_url': django_backend_service_api_url,
        'django_backend_service_url': django_backend_service_url,
        'config_path_work': config_path_work,
        'uploadFileForm': upload_file_form,
        'repr_dirs': repr_dir_names,
        'ip': ip,
        'rep': repname,
        'pk': pk,
        'form': form,
        'representations': reprs,
        'representations_directory': representations_directory,
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def upload_step5_rep(request, pk, rep):
    # create representation if it does not exist
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    # pylint: disable-next=no-member
    exists = Representation.objects.filter(ip=ip, identifier=rep)
    if not exists:
        # pylint: disable-next=no-member
        result = Representation.objects.create(ip=ip, identifier=rep)
        result.save()
    request.session['rep'] = rep
    return upload_step4(request, pk)


@login_required
def updatedistrmd(request):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=request.POST['pk'])
    rep = request.POST['rep']
    try:
        # pylint: disable-next=no-member
        result = Representation.objects.get(ip=ip, identifier=rep)
    except ObjectDoesNotExist:
        # pylint: disable-next=no-member
        result = Representation.objects.create(ip=ip, identifier=rep)
    param_name = request.POST['param_name']
    param_value = request.POST['param_value']
    result_dict = {param_name: param_value}
    if param_name == "distribution_label":
        result.label = param_value
    if param_name == "distribution_description":
        result.description = param_value
    if param_name == "access_rights":
        result.accessRights = param_value
    if param_name == "file_metadata":
        # Parse param_value from JSON string to dictionary
        param_value_dict = json.loads(param_value)

        # Load existing JSON metadata if it exists, otherwise start with an empty dictionary
        file_metadata = json.loads(result.file_metadata) if result.file_metadata else {}

        # Merge or update the JSON metadata
        for key, value in param_value_dict.items():
            file_metadata[key] = value  # This will add or update the key with the new value

        # Save the updated JSON back to the database field
        result.file_metadata = json.dumps(file_metadata)  # Convert dict to JSON string
    result.save()

    return JsonResponse(result_dict)


@login_required
def ip_creation_process(request, pk):
    try:
        # get ip
        # pylint: disable-next=no-member
        ip = InformationPackage.objects.get(pk=pk)

        finalization_time = date_format(datetime.datetime.utcnow(), fmt=DT_ISO_FORMAT) #  current_timestamp(fmt=DT_ISO_FORMAT)
        # merge posted data from step2 into one dictionary (ip.created,ip.last_change)

        if 'step1' not in request.session or not hasattr(request.session['step1'], 'items'):
            return redirect('submission:upload_step1', pk=pk)

        context = dict(
            chain(
                request.session['step1'].items(),
                request.session['step2'].items(),
                request.session['step3'].items(),
                request.session['step4'].items(),
                {"uid": ip.uid}.items(),
                {'currdate': ts_date(fmt=DT_ISO_FORMAT), 'date': ts_date(fmt=DATE_DMY), "last_change": finalization_time,
                 "created": finalization_time,
                 'landing_page': string.Template(package_access_url_pattern).substitute(
                     {'packageid': "%s" % ip.uid})
                 }.items()
            )
        )

        # pylint: disable-next=no-member
        reprecords = Representation.objects.filter(ip=ip)
        repinfo = {}

        for reprecord in reprecords:
            file_metadata = {}  
            try:
                # Ensure file_metadata is a valid dictionary
                file_metadata = json.loads(reprecord.file_metadata) if isinstance(reprecord.file_metadata, str) else reprecord.file_metadata
                if not isinstance(file_metadata, dict):
                    file_metadata = {}  # Ensure it's a dict
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for file_metadata in {reprecord.identifier}: {e}")
                file_metadata = {}  

            file_items = []
            data_path = os.path.join(config_path_work, ip.uid, representations_directory, reprecord.identifier, "data")
            for f in find_files(data_path, "*"):
                file_item = f.replace(data_path, "").strip("/")
                file_items.append(file_item)

                if os.path.exists(f):
                    # Ensure file_item exists in file_metadata before assignment
                    if file_item not in file_metadata:
                        file_metadata[file_item] = {}  # Initialize it as an empty dictionary

                    file_metadata[file_item]["bytesSize"] = os.path.getsize(f)
                    mime_type, _ = mimetypes.guess_type(f)
                    file_metadata[file_item]['mimeType'] = mime_type or 'application/octet-stream'

                    # Duration for media files
                    if mime_type:
                        try:
                            if mime_type.startswith('audio'):
                                audio = MutagenFile(f)
                                duration = audio.info.length if audio.info else None
                                file_metadata[file_item]['durationSeconds'] = round(duration, 2) if duration else None
                            elif mime_type.startswith('video'):
                                with VideoFileClip(f) as video:
                                    file_metadata[file_item]['durationSeconds'] = round(video.duration, 2)
                        except Exception as e:
                            logger.warning(f"Media type metadata cannot be extracted for {reprecord.identifier}: {e}")

            repinfo[reprecord.identifier] = {
                'distribution_label': reprecord.label,
                'distribution_description': reprecord.description,
                'access_rights': reprecord.accessRights,
                'file_metadata': file_metadata,
                'file_items': file_items
            }

        if reprecords:
            context = dict(chain(context.items(), {'representations': repinfo}.items()))

        basic_metadata = context

        context["node_namespace_id"] = node_namespace_id
        context["repo_id"] = repo_id
        context["repo_title"] = repo_title
        context["repo_description"] = repo_description
        context["repo_catalogue_issued"] = repo_catalogue_issued
        context["repo_catalogue_modified"] = repo_catalogue_modified

        lang = pycountry.languages.get(name=context['language'])
        context["lang_alpha_3"] = "eng" if not lang else lang.alpha_3

        basic_metadata.pop('csrfmiddlewaretoken', None)
        basic_metadata.pop('hidden_user_tags', None)
        basic_metadata.pop('currdate', None)
        basic_metadata.pop('pk', None)
        basic_metadata.pop('rep', None)
        basic_metadata_s = json.dumps(basic_metadata)

        ip.basic_metadata = basic_metadata_s
        ip.save()

        if "csrfmiddlewaretoken" in basic_metadata:
            del basic_metadata["csrfmiddlewaretoken"]
        if "hidden_user_tags" in basic_metadata:
            del basic_metadata["hidden_user_tags"]
        if "user_generated_tags" in basic_metadata:
            del basic_metadata["user_generated_tags"]
        if "currdate" in basic_metadata:
            del basic_metadata["currdate"]
        if "lang_alpha_3" in basic_metadata:
            del basic_metadata["lang_alpha_3"]
        if "landing_page" in basic_metadata:
            del basic_metadata["landing_page"]
        if "pk" in basic_metadata:
            del basic_metadata["pk"]
        if "rep" in basic_metadata:
            del basic_metadata["rep"]

        #  convert the JSON string into a Python list 
        basic_metadata["locations"] = json.loads(basic_metadata["locations"])

        basic_metadata["tags"] = [val.name for val in ip.tags.all()]
        basic_metadata_to_be_stored = dict_keys_underscore_to_camel(basic_metadata)

        ead_dir = 'earkweb'
        ead_path = os.path.join(ead_dir, 'ead.xml')


        #import lxml.etree as ET
        #pead = ParsedEad(ead_dir, ead_path)
        #ead_content = ET.tostring(pead.ead_tree.getroot(), encoding='UTF-8', pretty_print=True, xml_declaration=True)

        template = loader.get_template(ead_path)

        md_target_path = os.path.join(config_path_work, ip.uid, "metadata", 'metadata.json')
        md_content = json.dumps(basic_metadata_to_be_stored, indent=4)
        target_dir = os.path.dirname(md_target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        with open(md_target_path, 'w') as md_file:
            md_file.write(md_content)

        ead_content = template.render(context=context)
        ead_target_path = os.path.join(config_path_work, ip.uid, "metadata/descriptive", 'ead.xml')
        target_dir = os.path.dirname(ead_target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        with open(ead_target_path, 'w', encoding='utf-8') as md_file:
            md_file.write(ead_content)

        from rdflib import Graph, Literal, Namespace, URIRef
        from rdflib.namespace import DC, DCTERMS
        import urllib.parse

        # Create graph
        g = Graph()

        # Namespaces
        EX = Namespace(f"http://e-ark-foundation.eu/resource/{ip.uid}/")
        g.bind("dc", DC)
        g.bind("dcterms", DCTERMS)

        # URI for parent resource (Ybbs in your example)
        safe_title = urllib.parse.quote(basic_metadata["title"], safe='')
        parent_resource_uri = URIRef(EX[safe_title])

        # Add Dublin Core elements for parent resource
        g.add((parent_resource_uri, DC.title, Literal(basic_metadata["title"])))
        g.add((parent_resource_uri, DC.creator, Literal(basic_metadata["contact_point"])))
        g.add((parent_resource_uri, DC.description, Literal(basic_metadata["description"])))
        g.add((parent_resource_uri, DC.date, Literal(basic_metadata["created"])))

        # Add spatio-temporal data
        for location in basic_metadata["locations"]:
            label = location['label']
            coordinates = location['coordinates']
            lat = coordinates['lat']
            lng = coordinates['lng']
            zoom_level = location['zoomLevel']
            location_uncertainty = location['locationUncertainty']
            uncertainty_radius = location['locationUncertaintyRadius']
            if 'locationEvent' in location:
                # Record the ingestion event
                eventIdentifier = urn_event_pattern.format(
                    event_type=to_safe_filename(location['locationEvent']), 
                    quoted_identifier=quote(ip.identifier, safe=''), 
                    date_time_string=location['locationDate']
                )
                locationEvent = location['locationEvent']
                locationDate = location['locationDate']
                spatial_info = f"{label}, {lat}, {lng} ({zoom_level}, {location_uncertainty}, {uncertainty_radius}, {eventIdentifier}, {locationEvent}, {locationDate})"
                g.add((parent_resource_uri, DCTERMS.spatial, Literal(spatial_info)))
                g.add((parent_resource_uri, DCTERMS.temporal, Literal(basic_metadata["created"])))

        # Add child representations and hasPart relationships
        if "representations" in basic_metadata:
            for rep_id, rep_data in basic_metadata["representations"].items():
                child_resource_uri = URIRef(EX[rep_id])  # URI for the child (e.g., PDF representation)
                
                # Add metadata for each child resource (representation)
                g.add((child_resource_uri, DCTERMS.title, Literal(rep_data["distribution_label"])))
                g.add((child_resource_uri, DCTERMS.description, Literal(rep_data["distribution_description"])))
                g.add((child_resource_uri, DCTERMS.rights, Literal(rep_data["access_rights"])))
                
                # Add file items for each representation
                for file_path in rep_data["file_items"]:
                    file_uri = URIRef(EX[urllib.parse.quote(file_path)])
                    g.add((child_resource_uri, DCTERMS.hasPart, file_uri))

                # Link the child resource to the parent using hasPart
                g.add((parent_resource_uri, DCTERMS.hasPart, child_resource_uri))
                # Optionally, add the reverse relationship (isPartOf) from child to parent
                g.add((child_resource_uri, DCTERMS.isPartOf, parent_resource_uri))

        # Add producer and publisher
        g.add((parent_resource_uri, DCTERMS.contributor, Literal(basic_metadata["contact_point"])))
        g.add((parent_resource_uri, DCTERMS.publisher, Literal(basic_metadata["publisher"])))

        # Add license
        g.add((parent_resource_uri, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))

        # Serialize graph to Turtle file
        ttl_target_path = os.path.join(config_path_work, ip.uid, "metadata", 'metadata.ttl')
        g.serialize(ttl_target_path, format="turtle")

        logging.info(f"Turtle file written to: {ttl_target_path}")

        from taskbackend.tasks import sip_package
        task_input = {
            "package_name": ip.package_name, "uid": ip.uid, "org_nsid": "repo"
        }
        job = sip_package.delay(json.dumps(task_input))

        # unset session data
        request.session['step1'] = None
        request.session['step2'] = None
        request.session['representations'] = None
        schema, domain = get_domain_scheme(request.headers.get("Referer"))
        url = "%s://%s/earkweb/api/ips/%s/dir-json" % (schema, domain, ip.uid)
        user_api_token = get_user_api_token(request.user)
        response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)

        # render html page (finalization)
        context = {
            'uid': ip.uid,
            'config_path_work': config_path_work,
            'ip': ip,
            'pk': pk,
            "dirasjson": response.content.decode('utf-8'),
            "jobid": job.id,
            'flower_status': flower_is_running(),
            "django_backend_service_api_url": django_backend_service_api_url
        }
        template = loader.get_template('submission/ip_creation_process.html')
        return HttpResponse(template.render(context=context, request=request))
    except FileNotFoundError as err:
        logger.error("Missing file %s" % str(err))


@login_required
def upload_finalize(request, pk):
    # get ip
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    schema, domain = get_domain_scheme(request.headers.get("Referer"))
    url = "%s://%s/earkweb/api/ips/%s/dir-json" % (
       schema, domain, ip.uid)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)

    # render html page (finalization)
    context = {
        'uid': ip.uid,
        'config_path_work': config_path_work,
        'ip': ip,
        'pk': pk,
        "dirasjson": response.content.decode('utf-8'),
        "django_backend_service_api_url": django_backend_service_api_url
    }
    template = loader.get_template('submission/upload_finalize.html')
    return HttpResponse(template.render(context=context, request=request))


@login_required
def index(request):
    template = loader.get_template('submission/index.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


class InformationPackageTable(tables.Table):

    from django_tables2.utils import A
    area = "submission"
    last_change = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name=_('Last modified'), orderable=True)
    uid = tables.LinkColumn('%s:working_area' % area,
                                   kwargs={'section': area, 'uid': A('uid')},
                                   verbose_name=_('Working directory'), orderable=False,
                                   attrs={'a': {'data-toggle': 'tooltip', 'title': _('ShowWorkingDirectory')}})
    package_name = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name=_('Data Set Label'), orderable=True)

    edit = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name=_('Change'), orderable=False)
    ingest = tables.LinkColumn('%s:startingest' % area, kwargs={'pk': A('pk')}, verbose_name=_('Ingest'), orderable=False)
    delcol = tables.LinkColumn('%s:delete' % area, kwargs={'pk': A('pk')}, verbose_name=_('Delete'), orderable=False)

    class Meta:
        model = InformationPackage
        fields = ('package_name', 'uid', 'last_change', 'edit', 'ingest', 'delcol')
        attrs = {'class': 'table table-striped table-bordered table-condensed'}
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_edit(value):
        return mark_safe(value)
    
    @staticmethod
    def render_ingest(value):
        return mark_safe(value)

    @staticmethod
    def render_delcol(value):
        return mark_safe(value)

    @staticmethod
    def render_statusprocess(value):
        if value == "Success":
            return mark_safe(
                'Success <span class="fas fa-check-circle" aria-hidden="true" style="color:green"/>'
            )
        elif value == "Error":
            return mark_safe(
                'Error <span class="fas fa-exclamation-circle" aria-hidden="true" style="color:#91170A"/>'
            )
        elif value == "Warning":
            return mark_safe(
                'Warning <span class="fa-exclamation-triangle" aria-hidden="true" style="color:#F6A50B"/>'
            )
        else:
            return value


@login_required
@csrf_exempt
def informationpackages_overview(request):
    area = "submission"
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
    where storage_dir='' and 
    (ip.uid like '%%{0}%%' or ip.package_name like '%%{0}%%' or ip.identifier like '%%{0}%%')
    and deleted != 1
    order by ip.last_change desc;
    """.format(filterword, areacode)
    # user_id={0} and, request.user.pk
    # pylint: disable-next=no-member
    queryset = InformationPackage.objects.raw(sql_query)
    table = InformationPackageTable(queryset)
    RequestConfig(request, paginate={'per_page': 8}).configure(table)
    context = {
        'informationpackage': table,
    }
    if request.method == "POST":
        return render(request, 'earkweb/ipstable.html', context=context)
    else:
        return render(request, '%s/overview.html' % area, {'informationpackage': table})


@login_required
def sip_detail_rep(request, pk, rep):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('submission/detail.html')
    upload_file_form = TinyUploadFileForm()
    repr_dir = os.path.join(ip.work_dir, representations_directory)
    repr_dirs = filter(lambda x: os.path.isdir(os.path.join(repr_dir, x)), os.listdir(repr_dir))

    request.session['rep'] = rep

    context = {
        'uid': ip.uid,
        'config_path_work': config_path_work,
        'uploadFileForm': upload_file_form,
        'repr_dirs': repr_dirs,
        'ip': ip,
        'rep': rep,
        'pk': pk,
    }
    return HttpResponse(template.render(context=context, request=request))


class InformationPackageDetail(DetailView):
    """
    Information Package Detail View
    """
    model = InformationPackage
    context_object_name = 'ip'
    template_name = 'submission/detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InformationPackageDetail, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InformationPackageDetail, self).get_context_data(**kwargs)
        context['config_path_work'] = config_path_work
        try:
            context['metadata'] = json.loads(self.object.basic_metadata)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error loading metadata: {e}")

        # pylint: disable-next=no-member
        distributions = Representation.objects.filter(ip_id=self.object.pk).values()
        context['distributions'] = distributions
        return context


class StartIngestDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = InformationPackage
    context_object_name = 'ip'
    template_name = 'submission/start_ingest.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(StartIngestDetail, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StartIngestDetail, self).get_context_data(**kwargs)
        context['config_path_work'] = config_path_work
        context['celery_worker_status'] = get_celery_worker_status()
        context['flower_status'] = flower_is_running()
        context['flower_api_endpoint'] = flower_service_url
        context['django_backend_service_api_url'] = django_backend_service_api_url

        return context


@login_required
@csrf_exempt
def add_file(request, uid, subfolder):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(uid=uid)
    repname = ""
    if 'rep' in request.POST:
        repname = request.POST['rep']
    repsubdir = ""
    if 'subdir' in request.POST:
        repsubdir = request.POST['subdir']
    if subfolder.startswith("_root_"):
        subfolder = subfolder.replace("_root_", ".")
    ip_work_dir = os.path.join(config_path_work, uid)
    upload_path = os.path.join(ip_work_dir, subfolder, repname, repsubdir)
    print(upload_path)

    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)
    if request.method == 'POST':
        form = TinyUploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_aip(ip_work_dir, upload_path, request.FILES['content_file'])
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))
    if not repname and 'rep' in request.session:
        repname = request.session['rep']
    url = "/earkweb/submission/detail/%s/%s/" % (str(ip.id), repname)
    return HttpResponseRedirect(url)


def upload_aip(ip_work_dir, upload_path, f):
    print("Upload file '%s' to working directory: %s" % (f, upload_path))
    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)
    destination_file = os.path.join(upload_path, f.name)
    with open(destination_file, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()
    if f.name.endswith(".tar"):
        # pylint: disable-next=no-member
        async_res = extract_and_remove_package.delay(
            destination_file, upload_path, os.path.join(ip_work_dir, 'metadata/sip_creation.log'))
        print("Package extraction task '%s' to extract package '%s' to working directory: %s" % (
            async_res.id, f.name, upload_path))


@login_required
@require_http_methods(["POST"])
def initialize(request):
    package_name = request.POST["packagename"]
    extuid = encode_identifier(request.POST["extuid"])
    uid = get_unique_id()
    working_dir = os.path.join(config_path_work, uid)
    os.makedirs(os.path.join(working_dir, documentation_directory), exist_ok=True)
    os.makedirs(os.path.join(working_dir, representations_directory), exist_ok=True)
    os.makedirs(os.path.join(working_dir, metadata_directory), exist_ok=True)
    
    # pylint: disable-next=no-member
    InformationPackage.objects.create(work_dir=os.path.join(config_path_work, uid), uid=uid,
                                      package_name=package_name, external_id=extuid, user=request.user, version=0)
    
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(uid=uid)

    state_data = json.dumps({"version": 0, "last_change": date_format(datetime.datetime.utcnow(), fmt=DT_ISO_FORMAT)})
    os.makedirs(os.path.join(working_dir, "metadata/other"), exist_ok=True)
    with open(os.path.join(working_dir, "metadata/other/state.json"), 'w') as status_file:
        status_file.write(state_data)

    return redirect('submission:upload_step1', pk=ip.pk)

    # return render(request, upload_step1, context)
    #
    # return HttpResponse(str(ip.id))


@login_required
def delete(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('submission/deleted.html')
    if ip.uid:
        path = os.path.join(config_path_work, ip.uid)
        if os.path.exists(path):
            shutil.rmtree(path)
    context = {
        'uid': ip.uid,
    }
    ip.delete()
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def add_representation(request, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    # representation = request.POST['representation']
    representation = get_unused_identifier(request.user.id)
    # pylint: disable-next=no-member
    reprec = Representation.objects.create(ip=ip, identifier=representation, accessRights='free')
    reprec.save()
    data = {"success": True, "representation": representation}
    return JsonResponse(data)


@login_required
@csrf_exempt
def del_representation(request, uid, representation_id):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(uid=uid)
    if request.user != ip.user:
        return HttpResponseForbidden("Permission denied to delete this object")
    try:
        work_dir = os.path.join(config_path_work, uid)
        distribution_dir = os.path.join(work_dir, representations_directory, representation_id)
        if os.path.exists(distribution_dir):
            shutil.rmtree(distribution_dir)
        if not os.path.exists(distribution_dir):
            # pylint: disable-next=no-member
            reprec = Representation.objects.get(ip=ip, identifier=representation_id)
            reprec.delete()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False})
        # delete representation data (using backend api)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()


@login_required
@csrf_exempt
def ip_by_primary_key(_, pk):
    # pylint: disable-next=no-member
    ip = InformationPackage.objects.get(pk=pk)
    return HttpResponse(ip.uid)


@login_required
@csrf_exempt
def ins_file(request, uid, subfolder):
    repname = ""
    if 'rep' in request.POST:
        repname = request.POST['rep']
        print("repname=%s" % repname)

    repsubdir = ""
    if 'subdir' in request.POST:
        repsubdir = request.POST['subdir']
        print("repsubdir=%s" % repsubdir)

    if subfolder.startswith("_root_"):
        subfolder = subfolder.replace("_root_", ".")
        print("subfolder=%s" % subfolder)

    ip_work_dir = os.path.join(config_path_work, uid)
    upload_path = os.path.join(ip_work_dir, subfolder, repname, repsubdir)
    print("upload_path=%s" % upload_path)

    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)

    if request.method == 'POST':
        form = TinyUploadFileForm(request.POST, request.FILES)
        print(request.FILES)
        if form.is_valid():
            print("valid form")
            upload_aip(ip_work_dir, upload_path, request.FILES['content_file'])
        else:
            if form.errors:
                for error in form.errors:
                    print(str(error) + str(form.errors[error]))

    return HttpResponse("success")


# @login_required
# @csrf_exempt
# def poll_state(request):
#     data = {"success": False, "errmsg": "Unknown error"}
#     try:
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             if 'task_id' in request.POST.keys() and request.POST['task_id']:
#                 task_id = request.POST['task_id']
#                 task = AsyncResult(task_id)
#                 if task.state == "SUCCESS":
#                     aggr_log = '\n'.join(task.result.log)
#                     aggr_err = '\n'.join(task.result.err)
#                     data = {
#                         "success": True, "result": task.result.success,
#                         "state": task.state, "log": aggr_log, "err": aggr_err
#                     }
#                 elif task.state == "PROGRESS":
#                     data = {"success": True, "result": task.state, "state": task.state, "info": task.info}
#             else:
#                 data = {"success": False, "errmsg": "No task_id in the request"}
#         else:
#             data = {"success": False, "errmsg": "Not ajax"}
#     except Exception as err:
#         data = {"success": False, "errmsg": str(err)}
#         tb = traceback.format_exc()
#         logging.error(str(tb))
#     return JsonResponse(data)


class SipCreationBatchView(ListView):
    """
    Processing status
    """
    model = InformationPackage
    template_name = 'sipcreator/batch.html'
    context_object_name = 'sips'
    # pylint: disable-next=no-member
    queryset = InformationPackage.objects.all().order_by('last_change')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SipCreationBatchView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SipCreationBatchView, self).get_context_data(**kwargs)
        return context


@login_required
@csrf_exempt
def apply_task(request):
    """
    Execute selected task.
    @type request: django.core.handlers.wsgi.WSGIRequest
    @param request: Request
    @rtype: django.http.JsonResponse
    @return: JSON response (task execution metadata)
    """
    try:
        selected_ip = request.POST['selected_ip']
        # pylint: disable-next=no-member
        ip = InformationPackage.objects.get(pk=selected_ip)
        user = User.objects.get(pk=request.user.pk)
        logger.info("Task processing for process id: %s started by user %s", ip.uid, user.username)
        # the task is an update task if the object already has an identifier
        is_update_task = bool(ip.identifier)
        # identifier assignment
        identifier = decode_identifier(ip.external_id) if ip.external_id else ip.identifier \
            if ip.identifier else "urn:uuid:%s" % str(uuid.uuid4())
        encoded_identifier = encode_identifier(identifier) 
        ip.external_id = encoded_identifier
        ip.identifier = identifier
        ip.save()
        task_input = {
            "uid": ip.uid, 
            "package_name": ip.package_name, 
            "org_nsid": node_namespace_id,
            "identifier": identifier,
            "encoded_identifier": encoded_identifier,
            "md_format": "METS", 
            "is_update_task": is_update_task
        }
        data = execute_task(task_input)
    except Exception as err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        data = {"success": False, "errmsg": str(err), "errdetail": str(tb)}
        return JsonResponse(data, status=500)
    if "success" in data and data["success"]:
        return JsonResponse(data, status=200)
    else:
        return JsonResponse(data, status=500)


@login_required
@csrf_exempt
def poll_state(request):
    """
    @type request: django.core.handlers.wsgi.WSGIRequest
    @param request: Request
    @rtype: django.http.JsonResponse
    @return: JSON response (task state metadata)
    """
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                task_info = get_task_info(task.id)
                if task.state == "SUCCESS":
                    child_task_ids, task_status_from_result = get_task_info_from_child_tasks(task)
                    uid = task_info["uid"]
                    # pylint: disable-next=no-member
                    ip = InformationPackage.objects.get(uid=uid)
                    if "storage_dir" in task_status_from_result:
                        ip.storage_loc = task_status_from_result["storage_dir"]
                    #if "version" in task_status_from_result:
                    #    ip.version = int(task_status_from_result["version"])
                    ip.statusprocess = 0
                    ip.save()
                    data = {"success": True, "child_task_ids": child_task_ids, "state": task.state,
                            "task_list": get_task_list(task_id, ['file_migration'])}
                elif task.state == "FAILURE":
                    err_msg = 'Task execution error' \
                        if not (task.result and 'message' in task.result) else task.result['message']
                    data = {"success": False, "errmsg": err_msg}
                else:
                    progress = task.result['process_percent'] if task.result and 'process_percent' in task.result else 0
                    data = {"success": True, "result": task.state, "state": task.state, "progress": progress,
                            "task_list": get_task_list(task_id, ['file_migration'])}
            else:
                data = {"success": False, "errmsg": "No task_id in the request"}
        else:
            data = {"success": False, "errmsg": "Not ajax"}
    except Exception as err:
        logger.error(err)
        data = {"success": False, "errmsg": str(err)}
    return JsonResponse(data, status=200)

def get_autocomplete(request):
    eurovoc_terms = list(Vocabulary.objects.values_list('term', flat=True))
    terms = eurovoc_terms
    if "term" in request.GET and request.GET["term"]:
        suggested_terms = [term for term in terms if term.startswith(request.GET["term"])]
    else:
        suggested_terms = terms
    return JsonResponse(suggested_terms, safe=False)


def get_autocomplete_tags(request):
    eurovoc_terms = list(Vocabulary.objects.values_list('term', flat=True))
    return JsonResponse(eurovoc_terms, safe=False)


def search_wikidata(query):
    """Function to search Wikidata"""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": query
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return [
            {
                "label": item.get("label", "Unknown"),
                "id": item["id"],
                "link": f"https://www.wikidata.org/wiki/{item['id']}"  # Convert to full URL
            }
            for item in response.json().get("search", [])
        ]
    
    return []


def search_gnd(query):
    """Function to search GND (German National Library)"""
    url = f"https://lobid.org/gnd/search?q={query}&format=json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  

        data = response.json()
        logger.info("GND API Response: %s", data)  

        if "member" not in data:  
            return []

        return [
            {
                "label": entry.get("preferredName", "Unknown"),
                "id": entry["id"],
                "link": entry["id"]
            }
            for entry in data.get("member", [])
        ]
    except requests.exceptions.RequestException as e:
        logger.error("Error fetching GND data: %s", e)
        return [] 

@login_required
@csrf_exempt
def search_ld(request):
    query = request.GET.get('q', '')
    search_gnd_enabled = request.GET.get('gnd', 'true') == 'true'
    search_wd_enabled = request.GET.get('wd', 'true') == 'true' 
    wikidata_results = []
    gnd_results = []

    if query:
        if search_wd_enabled:
            wikidata_results = search_wikidata(query)
        if search_gnd_enabled:
            gnd_results = search_gnd(query)

    return JsonResponse({
        'query': query,
        'wikidata_results': wikidata_results,
        'gnd_results': gnd_results
    })