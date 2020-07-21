import json
import os
from json import JSONDecodeError

from django.template import loader
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from shutil import rmtree

from eatb.storage.directorypairtreestorage import VersionDirFormat

from earkweb.models import InformationPackage, Representation
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from taskbackend.taskutils import extract_and_remove_package, flower_is_running

from config.configuration import config_path_work, verify_certificate
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django_tables2 import RequestConfig
from uuid import uuid4

import logging
from submission.views import upload_step1
from util.djangoutils import get_user_api_token

logger = logging.getLogger(__name__)

from django.utils.translation import ugettext_lazy as _


@login_required
def index(request):
    template = loader.get_template('management/index.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
@csrf_exempt
def ip_detail_table(request):
    logger.info("Updating ip table ...")
    pkg_id = request.POST['pkg_id']
    ip = InformationPackage.objects.get(pk=pkg_id)
    logger.info("- version: %s" % ip.version)
    context = {
        "ip": ip,
        "config_path_work": config_path_work
    }
    return render(request, 'management/iptable.html', context=context)


@login_required
def index(request):
    template = loader.get_template('management/index.html')
    context = {

    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def sip_detail(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    if not ip.process_id:
        context = {"ip": ip}
        return render(request, 'management/checkout.html', context=context)
    return upload_step1(request, pk)


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
        async_res = extract_and_remove_package.delay(destination_file, upload_path,
                                                     os.path.join(ip_work_dir, 'metadata/sip_creation.log'))
        print("Package extraction task '%s' to extract package '%s' to working directory: %s" % (
            async_res.id, f.name, upload_path))


@login_required
def delete(request, pk):
    ip = InformationPackage.objects.get(pk=pk)
    template = loader.get_template('management/deleted.html')
    if ip.process_id:
        path = os.path.join(config_path_work, ip.process_id)
        if os.path.exists(path):
            rmtree(path)
    context = {
        'process_id': ip.process_id,
    }
    ip.process_id = ""
    ip.work_dir = ""
    ip.save()
    return HttpResponse(template.render(context=context, request=request))


@login_required
def checkout(request, identifier):
    ip = InformationPackage.objects.get(identifier=identifier)
    process_id = None
    if not ip.process_id:
        process_id = str(uuid4())
        ip.process_id = process_id
        ip.work_dir = os.path.join(config_path_work, process_id)
    template = loader.get_template('management/checkout_confirm.html')
    from config.configuration import django_backend_service_host, django_backend_service_port
    import requests
    reset_aip = "reset_aip" in request.POST and request.POST["reset_aip"] == "on"
    request_url = "http://%s:%s/earkweb/api/informationpackages/%s/checkout-working-copy/?reset=%s" % \
                  (django_backend_service_host, django_backend_service_port, identifier, str(reset_aip).lower())
    user_api_token = get_user_api_token(request.user)
    response = requests.post(request_url, headers={'Authorization': 'Token %s' % user_api_token},
                             verify=verify_certificate)
    if response.status_code != 201:
        err_msg = "An error occurred while trying do the checkout"
        try:
            json_err = json.loads(response.text)
            err_msg = "%s: %s" % (err_msg, json_err["message"])
        except JSONDecodeError:
            pass
        return render(request, 'earkweb/error.html', {
            'header': 'Checkout error', 'message': err_msg
        })
    resp_json = json.loads(response.text)
    context = {
        'msg_checkout_confirm': resp_json['message'],
        'identifier': identifier,
        'process_id': process_id,
        'ip': ip,
        "jobid": resp_json["job_id"],
        'flower_status': flower_is_running()
    }
    return HttpResponse(template.render(context=context, request=request))


class InformationPackageTable(tables.Table):
    from django_tables2.utils import A
    area = "management"

    identifier = tables.LinkColumn('%s:storage_area' % area, kwargs={'section': area, 'identifier': A('identifier')},
                                   verbose_name=_("Archived Information Package"),
                                   attrs={'a': {'data-toggle': 'tooltip', 'title': _('PackageDirectory')}})
    version = tables.Column(verbose_name='Version')
    created = tables.DateTimeColumn(format="d.m.Y H:i:s", verbose_name=_("CreationDateTime"))
    packagecol = tables.Column(verbose_name=_('WorkingCopy'))
    package_name = tables.LinkColumn('%s:resubmit' % area, kwargs={'pk': A('pk')}, verbose_name=_("InternalLabel"),
                                     attrs={'a': {'data-toggle': 'tooltip', 'title': _('PackageOverview')}})
    edit = tables.LinkColumn('%s:ip_detail' % area, kwargs={'pk': A('pk')}, verbose_name=_('ChangeIt'))

    class Meta:
        model = InformationPackage
        fields = ('package_name', 'packagecol', 'identifier', 'version', 'created', 'edit')
        attrs = {'class': 'table table-striped table-bordered table-condensed'}
        row_attrs = {'data-id': lambda record: record.pk}

    @staticmethod
    def render_version(value):
        return VersionDirFormat % value

    @staticmethod
    def render_edit(value):
        return mark_safe(value)

    @staticmethod
    def render_packagecol(value):
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
    area = "management"
    areacode = "2"
    filterword = request.POST['filterword'] if 'filterword' in request.POST.keys() else ""
    sql_query = """
    select ip.id as id, ip.work_dir as path, ip.process_id as process_id, ip.package_name as package_name,
    CONCAT('<a href="/earkweb/management/modify/',ip.id,'/" data-toggle="tooltip" title="Metadaten ändern oder neue Version übertragen"><i class="glyphicon glyphicon-edit editcol"></i></a>') as edit,
    CONCAT('<a href="/earkweb/management/working_area/management/',ip.process_id,'/" data-toggle="tooltip" title="View working directory">',ip.process_id,'</a><a href="/earkweb/management/delete/',ip.id,'/" data-toggle="tooltip" title="Remove working copy">', IF(process_id IS NULL OR process_id = '', '', '<i class="glyphicon glyphicon-trash editcol"></i>'), '</a>') as packagecol,
    ip.identifier as identifier
    from informationpackage as ip
    where storage_dir != '' and not deleted > 0 and (ip.process_id like '%%{0}%%' or ip.package_name like '%%{0}%%' or ip.identifier like '%%{0}%%')
    order by ip.last_change desc;
    """.format(filterword, areacode)
    # user_id={0} and, request.user.pk
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


def upload_file(upload_path, f):
    print("Upload file '%s' to working directory: %s" % (f.name, upload_path))
    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)
    destination_file = os.path.join(upload_path, f.name)
    with open(destination_file, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()


class InformationPackageDetail(DetailView):
    """
    Information Package Detail View
    """
    model = InformationPackage
    context_object_name = 'ip'
    template_name = 'management/detail.html'

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
