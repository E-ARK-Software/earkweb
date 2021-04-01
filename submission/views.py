import datetime
import json
import os
import shutil
import string
import traceback
import logging
import uuid
from xml.etree import ElementTree

import django_tables2 as tables
import pycountry
import requests
import simplejson
from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig

from earkweb.views import get_domain_scheme
from eatb.metadata.parsedead import ParsedEad
from eatb.utils.datetime import current_timestamp, DT_ISO_FORMAT, ts_date, DATE_DMY, date_format
from eatb.utils.dictutils import dict_keys_underscore_to_camel, dict_keys_camel_to_underscore
from eatb.utils.randomutils import get_unique_id
from eatb.utils.fileutils import get_immediate_subdirectories, find_files

from config.configuration import representations_directory, \
    django_backend_service_host, django_backend_service_port, flower_service_url, node_namespace_id, \
    package_access_url_pattern, repo_identifier, repo_title, repo_description, repo_catalogue_issued, \
    repo_catalogue_modified, \
    verify_certificate, django_backend_service_api_url, metadata_directory, django_backend_service_url, root_dir
from config.configuration import config_path_work
from earkweb.models import Representation, InternalIdentifier, Vocabulary
from taskbackend.taskexecution import execute_task
from util.custom_exceptions import ResourceNotAvailable, AuthenticationError
from util.djangoutils import get_unused_identifier, get_user_api_token
from taskbackend.taskutils import extract_and_remove_package, update_states_from_backend_api, \
    get_celery_worker_status, flower_is_running, get_task_info_from_child_tasks

from rdflib import Literal
from submission.forms import MetaFormStep1, MetaFormStep2, TinyUploadFileForm, MetaFormStep4

from config.configuration import django_service_host
from config.configuration import django_service_port

from earkweb.models import InformationPackage
from itertools import chain

from django.utils.translation import ugettext_lazy as _

from util.flowerapiclient import get_task_info, get_task_list

logger = logging.getLogger(__name__)

# get eurovoc terms
eurovoc_terms = list(Vocabulary.objects.values_list('term', flat=True))


@login_required
@csrf_exempt
def ip_detail_table(request):
    pkg_id = request.POST['pkg_id']
    ip = InformationPackage.objects.get(pk=pkg_id)
    context = {
        "ip": ip,
        "config_path_work": config_path_work
    }
    return render(request, 'submission/iptable.html', context=context)


@login_required
def start(request):
    template = loader.get_template('submission/start.html')
    int_ids = InternalIdentifier.objects.filter(user=request.user.id, used=0)
    int_ids_values = int_ids.values()
    num_blockchain_ids = len([i for i in int_ids_values if i['is_blockchain_id'] == 1])
    num_selfgen_ids = len([i for i in int_ids_values if i['is_blockchain_id'] == 0])
    context = {
        'num_int_ids': len(int_ids),
        'num_blockchain_ids': num_blockchain_ids,
        'num_selfgen_ids': num_selfgen_ids
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def fileresource(request, item, ip_sub_file_path):
    user_api_token = get_user_api_token(request.user)
    schema, domain = get_domain_scheme(request.headers.get("Referer"))
    url = "%s://%s/earkweb/api/informationpackages/%s/file-resource/%s/" % (
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
def upload(request):
    if request.method == "POST":
        posted_files = request.FILES
        if 'file_data' not in posted_files:
            return JsonResponse({'error': "No files available"}, status=500)
        else:
            # distribution metadata
            rep = request.POST["rep"]
            # get information package
            ip = InformationPackage.objects.get(process_id=request.POST["process_id"])
            try:
                reprec = Representation.objects.get(ip=ip, identifier=rep)
            except ObjectDoesNotExist:
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

            ip = InformationPackage.objects.get(process_id=request.POST['process_id'])
            u = User.objects.get(username=request.user)
            # if u != ip.user:
            #    return JsonResponse({'error': "Unauthorized. Operation is not permitted."}, status=500)
            ip_work_dir = os.path.join(config_path_work, request.POST['process_id'])
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


def upload_step1(request, pk):

    ip = InformationPackage.objects.get(pk=pk)
    if "package_name" in request.POST and request.POST["package_name"] != ip.package_name:
        ip.package_name = request.POST["package_name"]
        ip.save()
    if "external_id" in request.POST and request.POST["external_id"] != ip.external_id:
        ip.external_id = request.POST["external_id"]
        ip.save()
    user_api_token = get_user_api_token(request.user)
    dir_info_request_url = "%s/informationpackages/%s/dir-json" % (django_backend_service_api_url, ip.process_id)
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
        data4 = {key: Literal(val) if isinstance(val, list) else Literal(val) for key, val in data3.items()}
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
        if ip.basic_metadata and ip.basic_metadata != 'null':
            md_properties = json.loads(ip.basic_metadata)

            md_properties = dict_keys_camel_to_underscore(md_properties)

            request.session['md_properties'] = md_properties
            # load existing metadata values as initial form values
            form = MetaFormStep1(initial={
                'package_name': ip.package_name,
                'external_id': ip.external_id,
                'title': md_properties["title"],
                'description': md_properties["description"]
            })
        else:
            form = MetaFormStep1(initial={
                'package_name': ip.package_name,
                'external_id': ip.external_id,
            })
        return render(request, 'submission/upload_mdform.html', {
            'form': form,
            'ip': ip,
            'tags': [val.name for val in ip.tags.all()],
            'user_generated_tags': user_generated_tags
        })


def upload_step2(request, pk):
    ip = InformationPackage.objects.get(pk=pk)

    if request.method == 'POST':

        form = MetaFormStep2(request.POST)
        data2 = request.POST
        data3 = dict(data2.items())
        data4 = {key: Literal(val[0]) if isinstance(val, list) else Literal(val) for key, val in data3.items()}
        if form.is_valid():
            request.session['step2'] = data4
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
            form = MetaFormStep2(initial={
                'contact_point': contact_point,
                'contact_email': contact_email,
                'publisher': publisher,
                'publisher_email': publisher_email,
                'language': language,

            })
        else:
            form = MetaFormStep2()
    return render(request, 'submission/upload_mdform.html', {'form': form, 'ip': ip})


@login_required
def upload_step4(request, pk):
    ip = InformationPackage.objects.get(pk=pk)

    template = loader.get_template('submission/upload_distributions.html')
    upload_file_form = TinyUploadFileForm()

    reprs_qs = Representation.objects.filter(ip=ip).order_by('id')

    # get representation from session or first reprsentation otherwise
    # if there is no representation, assign an unused identifier
    if "rep" in request.session:
        repname = request.session["rep"]
    elif reprs_qs:
        repname = reprs_qs[0].identifier
    else:
        representations_path = os.path.join(config_path_work, ip.process_id, representations_directory)
        representation_dirs = get_immediate_subdirectories(representations_path)
        if representation_dirs:
            repname = representation_dirs[0]
            try:
                Representation.objects.get(ip=ip, identifier=repname)
            except ObjectDoesNotExist:
                Representation.objects.create(ip=ip, identifier=repname)
        else:
            repname = get_unused_identifier(request.user.id)

    reprs_qs = Representation.objects.filter(ip=ip).order_by('id')

    repr_dir_names = None
    reprs = {}
    if repname:
        reprs = {
            r['identifier']: r for r in list(
                reprs_qs.values("id", "identifier", "label", "description", "license", "accessRights")
            )
        }
        repr_dir_names = list(reprs_qs.values_list('identifier', flat=True))
        if repname in reprs:
            curr_repr = reprs[repname]
            form = MetaFormStep4(initial={
                    'distribution_description': curr_repr['description'],
                    'distribution_label': curr_repr['label'],
                    'access_rights': curr_repr['accessRights'],
                })
        else:
            form = MetaFormStep4(request.POST)
    else:
        form = MetaFormStep4(request.POST)

    context = {
        'process_id': ip.process_id,
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
def upload_step4_rep(request, pk, rep):
    # create representation if it does not exist
    ip = InformationPackage.objects.get(pk=pk)
    exists = Representation.objects.filter(ip=ip, identifier=rep)
    if not exists:
        result = Representation.objects.create(ip=ip, identifier=rep)
        result.save()
    request.session['rep'] = rep
    return upload_step4(request, pk)


@login_required
def updatedistrmd(request):
    ip = InformationPackage.objects.get(pk=request.POST['pk'])
    rep = request.POST['rep']
    try:
        result = Representation.objects.get(ip=ip, identifier=rep)
    except ObjectDoesNotExist:
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
    result.save()

    return JsonResponse(result_dict)


@login_required
def ip_creation_process(request, pk):
    try:
        # get ip
        ip = InformationPackage.objects.get(pk=pk)

        finalization_time = date_format(datetime.datetime.utcnow(), fmt=DT_ISO_FORMAT) #  current_timestamp(fmt=DT_ISO_FORMAT)
        # merge posted data from step2 into one dictionary (ip.created,ip.last_change)

        if 'step1' not in request.session or not hasattr(request.session['step1'], 'items'):
            return redirect('submission:upload_step1', pk=pk)

        context = dict(
            chain(
                request.session['step1'].items(),
                request.session['step2'].items(),
                {"process_id": ip.process_id}.items(),
                {'currdate': ts_date(fmt=DT_ISO_FORMAT), 'date': ts_date(fmt=DATE_DMY), "last_change": finalization_time,
                 "created": finalization_time,
                 'landing_page': string.Template(package_access_url_pattern).substitute(
                     {'packageid': "%s" % ip.process_id})
                 }.items()
            )
        )

        reprecords = Representation.objects.filter(ip=ip)
        repinfo = {reprecord.identifier: {
            'distribution_label': reprecord.label,
            'distribution_description': reprecord.description,
            'access_rights': reprecord.accessRights,
            'file_items': [f.replace(os.path.join(config_path_work, ip.process_id), "").strip("/")
                           for f in find_files(os.path.join(config_path_work, ip.process_id, representations_directory,
                                                            reprecord.identifier, "data"), "*")]
        } for reprecord in reprecords}


        if reprecords:
            context = dict(chain(context.items(), {'representations': repinfo}.items()))

        basic_metadata = context

        context["node_namespace_id"] = node_namespace_id
        context["repo_identifier"] = repo_identifier
        context["repo_title"] = repo_title
        context["repo_description"] = repo_description
        context["repo_catalogue_issued"] = repo_catalogue_issued
        context["repo_catalogue_modified"] = repo_catalogue_modified

        lang = pycountry.languages.get(name=context['language'])
        context["lang_alpha_3"] = "eng" if not lang else lang.alpha_3


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

        basic_metadata["tags"] = [val.name for val in ip.tags.all()]
        basic_metadata_to_be_stored = dict_keys_underscore_to_camel(basic_metadata)

        ead_dir = 'earkweb'
        ead_path = os.path.join(ead_dir, 'ead.xml')


        #import lxml.etree as ET
        #pead = ParsedEad(ead_dir, ead_path)
        #ead_content = ET.tostring(pead.ead_tree.getroot(), encoding='UTF-8', pretty_print=True, xml_declaration=True)

        template = loader.get_template(ead_path)

        ead_content = template.render(context=context)

        files = {
            'jsonmd': ('metadata.json', json.dumps(basic_metadata_to_be_stored, indent=4)),
            'eadmd': ('descriptive/ead.xml', ead_content)
        }
        request_url = "%s/informationpackages/%s/metadata/upload/" % (django_backend_service_api_url, ip.process_id)
        user_api_token = get_user_api_token(request.user)
        response = requests.post(request_url, files=files, headers={'Authorization': 'Token %s' % user_api_token},
                                 verify=verify_certificate)
        if response.status_code != 201:
            return render(request, 'earkweb/error.html', {
                'header': 'Error uploading metadata (%d)' % response.status_code, 'message': response.text
            })

        from taskbackend.tasks import sip_package
        task_input = {
            "package_name": ip.package_name, "process_id": ip.process_id, "org_nsid": "repo"
        }
        job = sip_package.delay(json.dumps(task_input))

        # unset session data
        request.session['step1'] = None
        request.session['step2'] = None
        request.session['representations'] = None
        schema, domain = get_domain_scheme(request.headers.get("Referer"))
        url = "%s://%s/earkweb/api/informationpackages/%s/dir-json" % (schema, domain, ip.process_id)
        user_api_token = get_user_api_token(request.user)
        response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)

        # render html page (finalization)
        context = {
            'process_id': ip.process_id,
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
        logger.error("Missing file", err)


@login_required
def upload_finalize(request, pk):
    # get ip
    ip = InformationPackage.objects.get(pk=pk)

    url = "/earkweb/api/informationpackages/%s/dir-json" % (
       ip.process_id)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)

    # render html page (finalization)
    context = {
        'process_id': ip.process_id,
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
    process_id = tables.LinkColumn('%s:working_area' % area,
                                   kwargs={'section': area, 'process_id': A('process_id')},
                                   verbose_name=_('Working directory'), orderable=False,
                                   attrs={'a': {'data-toggle': 'tooltip', 'title': _('ShowWorkingDirectory')}})
    package_name = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name=_('Data Set Label'), orderable=True)

    edit = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name=_('Change'), orderable=False)
    delcol = tables.LinkColumn('%s:delete' % area, kwargs={'pk': A('pk')}, verbose_name=_('Delete'), orderable=False)

    class Meta:
        model = InformationPackage
        fields = ('package_name', 'process_id', 'last_change', 'edit', 'delcol')
        attrs = {'class': 'table table-striped table-bordered table-condensed'}
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_edit(value):
        return mark_safe(value)

    @staticmethod
    def render_delcol(value):
        return mark_safe(value)

    @staticmethod
    def render_statusprocess(value):
        if value == "Success":
            return mark_safe(
                'Success <span class="glyphicon glyphicon-ok-sign" aria-hidden="true" style="color:green"/>'
            )
        elif value == "Error":
            return mark_safe(
                'Error <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true" style="color:#91170A"/>'
            )
        elif value == "Warning":
            return mark_safe(
                'Warning <span class="glyphicon glyphicon-warning-sign" aria-hidden="true" style="color:#F6A50B"/>'
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
    select ip.id as id, ip.work_dir as path, ip.process_id as process_id, ip.package_name as package_name, 
    ip.identifier as identifier,
    CONCAT('<a href="/earkweb/submission/upload_step1/',ip.id,'/" data-toggle="tooltip" title="Change">
    <i class="glyphicon glyphicon-edit editcol"></i></a>') as edit,
    CONCAT('<a href="/earkweb/submission/delete/',ip.id,'/" data-toggle="tooltip" title="Delete">
    <i class="glyphicon glyphicon-remove editcol"></i></a>') as delcol 
    from informationpackage as ip
    where storage_dir='' and 
    (ip.process_id like '%%{0}%%' or ip.package_name like '%%{0}%%' or ip.identifier like '%%{0}%%')
    and deleted != 1
    order by ip.last_change desc;
    """.format(filterword, areacode)
    # user_id={0} and, request.user.pk
    print(sql_query)
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
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('submission/detail.html')
    upload_file_form = TinyUploadFileForm()
    repr_dir = os.path.join(ip.work_dir, representations_directory)
    repr_dirs = filter(lambda x: os.path.isdir(os.path.join(repr_dir, x)), os.listdir(repr_dir))

    request.session['rep'] = rep

    context = {
        'process_id': ip.process_id,
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
        context['metadata'] = json.loads(self.object.basic_metadata)

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
def add_file(request, process_id, subfolder):
    ip = InformationPackage.objects.get(process_id=process_id)
    repname = ""
    if 'rep' in request.POST:
        repname = request.POST['rep']
    repsubdir = ""
    if 'subdir' in request.POST:
        repsubdir = request.POST['subdir']
    if subfolder.startswith("_root_"):
        subfolder = subfolder.replace("_root_", ".")
    ip_work_dir = os.path.join(config_path_work, process_id)
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
        async_res = extract_and_remove_package.delay(
            destination_file, upload_path, os.path.join(ip_work_dir, 'metadata/sip_creation.log'))
        print("Package extraction task '%s' to extract package '%s' to working directory: %s" % (
            async_res.id, f.name, upload_path))


@login_required
@csrf_exempt
def initialize(request, package_name, extuid):
    process_id = get_unique_id()
    working_dir = os.path.join(config_path_work, process_id)
    os.makedirs(os.path.join(working_dir, representations_directory), exist_ok=True)
    os.makedirs(os.path.join(working_dir, metadata_directory), exist_ok=True)
    InformationPackage.objects.create(work_dir=os.path.join(config_path_work, process_id), process_id=process_id,
                                      package_name=package_name, external_id=extuid, user=request.user, version=0)
    ip = InformationPackage.objects.get(process_id=process_id)

    state_data = json.dumps({"version": 0, "last_change": date_format(datetime.datetime.utcnow(), fmt=DT_ISO_FORMAT)})
    with open(os.path.join(working_dir, "state.json"), 'w') as status_file:
        status_file.write(state_data)

    return HttpResponse(str(ip.id))


@login_required
def delete(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('submission/deleted.html')
    if ip.process_id:
        path = os.path.join(config_path_work, ip.process_id)
        if os.path.exists(path):
            shutil.rmtree(path)
    context = {
        'process_id': ip.process_id,
    }
    ip.delete()
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def add_representation(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    # representation = request.POST['representation']
    representation = get_unused_identifier(request.user.id)
    reprec = Representation.objects.create(ip=ip, identifier=representation, accessRights='free')
    reprec.save()
    data = {"success": True, "representation": representation}
    return JsonResponse(data)


@login_required
@csrf_exempt
def del_representation(request, process_id, representation_id):
    ip = InformationPackage.objects.get(process_id=process_id)
    if request.user != ip.user:
        return HttpResponseForbidden("Permission denied to delete this object")
    try:
        work_dir = os.path.join(config_path_work, process_id)
        distribution_dir = os.path.join(work_dir, representations_directory, representation_id)
        if os.path.exists(distribution_dir):
            shutil.rmtree(distribution_dir)
        if not os.path.exists(distribution_dir):
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
    ip = InformationPackage.objects.get(pk=pk)
    return HttpResponse(ip.process_id)


@login_required
@csrf_exempt
def ins_file(request, process_id, subfolder):
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

    ip_work_dir = os.path.join(config_path_work, process_id)
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


@login_required
@csrf_exempt
def poll_state(request):
    data = {"success": False, "errmsg": "Unknown error"}
    try:
        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                if task.state == "SUCCESS":
                    aggr_log = '\n'.join(task.result.log)
                    aggr_err = '\n'.join(task.result.err)
                    data = {
                        "success": True, "result": task.result.success,
                        "state": task.state, "log": aggr_log, "err": aggr_err
                    }
                elif task.state == "PROGRESS":
                    data = {"success": True, "result": task.state, "state": task.state, "info": task.info}
            else:
                data = {"success": False, "errmsg": "No task_id in the request"}
        else:
            data = {"success": False, "errmsg": "Not ajax"}
    except Exception as err:
        data = {"success": False, "errmsg": str(err)}
        tb = traceback.format_exc()
        logging.error(str(tb))
    return JsonResponse(data)


class SipCreationBatchView(ListView):
    """
    Processing status
    """
    model = InformationPackage
    template_name = 'sipcreator/batch.html'
    context_object_name = 'sips'

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
        ip = InformationPackage.objects.get(pk=selected_ip)
        user = User.objects.get(pk=request.user.pk)
        logger.info("Task processing for process id: %s started by user %s" % (ip.process_id, user.username))
        # the task is an update task if the object already has an identifier
        is_update_task = ip.identifier
        # identifier assignment (urn:uuid:<uuid>)
        identifier = ip.identifier if ip.identifier else "urn:uuid:%s" % uuid.uuid4().__str__()
        ip.identifier = identifier
        ip.save()
        task_input = {
            "process_id": ip.process_id, "package_name": ip.package_name, "org_nsid": node_namespace_id,
            "identifier": identifier, "md_format": "METS", "is_update_task": is_update_task}
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
        if request.is_ajax():
            if 'task_id' in request.POST.keys() and request.POST['task_id']:
                task_id = request.POST['task_id']
                task = AsyncResult(task_id)
                task_info = get_task_info(task.id)
                if task.state == "SUCCESS":
                    child_task_ids, task_status_from_result = get_task_info_from_child_tasks(task)
                    process_id = task_info["process_id"]
                    ip = InformationPackage.objects.get(process_id=process_id)
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

    terms = eurovoc_terms
    if "term" in request.GET and request.GET["term"]:
        suggested_terms = [term for term in terms if term.startswith(request.GET["term"])]
    else:
        suggested_terms = terms
    return JsonResponse(suggested_terms, safe=False)


def get_autocomplete_tags(request):
    return JsonResponse(eurovoc_terms, safe=False)
