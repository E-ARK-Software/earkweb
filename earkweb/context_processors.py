from config.configuration import flower_host, flower_port, flower_path, sw_version, sw_version_date, is_test_instance, \
    logo, repo_title, repo_description
import json
import string

import requests
from django.utils import translation

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def environment_variables(request):
    lang = request.META['HTTP_ACCEPT_LANGUAGE'][0:2] if 'HTTP_ACCEPT_LANGUAGE' in request.META else "en"
    if settings.LANGUAGE_CODE in request.session:
        lang = request.session[settings.LANGUAGE_CODE]
    return {'logo': logo,
            'repo_title': repo_title,
            'repo_description': repo_description,
            'sw_version': sw_version,
            'sw_version_date': sw_version_date,
            'is_test_instance': is_test_instance,
            'lang': lang,
            'flower_host': flower_host, 'flower_port': flower_port, 'flower_path': flower_path,
            'MEDIA_URL': settings.MEDIA_URL}
