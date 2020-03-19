#!/usr/bin/env python
# coding=UTF-8
import json
import logging

import requests
from django.core import serializers
from django.http import HttpResponseNotFound
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from eatb.utils.datetime import ts_date, DT_ISO_FORMAT, date_format

from earkweb.models import InformationPackage
from resourcesync.change_type import ChangeType
from util.djangoutils import get_user_api_token

from config.configuration import django_service_host, django_backend_service_host, django_backend_service_port, \
    verify_certificate
from config.configuration import django_service_port

logger = logging.getLogger(__name__)


def index(request):
    context = {
        'currdate': ts_date(fmt=DT_ISO_FORMAT),
        "django_service_host": django_service_host,
        "django_service_port": django_service_port,
    }
    content = render(request=request, template_name='resourcesync/index.xml', context=context)
    return HttpResponse(content=content, content_type='application/xml; charset="utf-8')


def changelist(request):
    resources = []
    for ip in InformationPackage.objects.exclude(identifier='').exclude(storage_dir=''):
        if ip.deleted:
            change_type = ChangeType.str(ChangeType.DELETED)
        else:
            if ip.last_change > ip.created:
                change_type = ChangeType.str(ChangeType.UPDATED)
            else:
                change_type = ChangeType.str(ChangeType.CREATED)
        dt = ip.last_change
        formatted_date = date_format(ip.last_change)
        resources.append({"identifier": ip.identifier, "last_change": formatted_date, "change_type": change_type})
    context = {
        'currdate': ts_date(fmt=DT_ISO_FORMAT),
        "django_service_host": django_service_host,
        "django_service_port": django_service_port,
        "resources": resources
    }
    content = render(request=request, template_name='resourcesync/changelist.xml', context=context)
    return HttpResponse(content=content, content_type='application/xml; charset="utf-8')


def resource(request, identifier):

    ips = InformationPackage.objects.filter(identifier=identifier).order_by('-id')
    if len(ips) == 0:
        return HttpResponseNotFound()
    if len(ips) > 1:
        logger.warning("More than one record exists for identifier: %s" % identifier)
    ip = ips[0]
    # try mapped metadata file, if it does not exist, the original metadata file is returned
    content_type = "application/json; charset=utf-8"
    content = {"status": ip}

    qs_json = serializers.serialize('json', ips)

    #return HttpResponse(qs_json, content_type='application/json')
    return JsonResponse(json.loads(qs_json), content_type=content_type, safe=False)
