from config.configuration import flower_server, flower_port, flower_path, sw_version, sw_version_date, is_test_instance
import json
import string

import requests
from django.utils import translation

import logging

logger = logging.getLogger(__name__)


def environment_variables(request):
    lang = request.META['HTTP_ACCEPT_LANGUAGE'][0:2] if 'HTTP_ACCEPT_LANGUAGE' in request.META else "de"
    if translation.LANGUAGE_SESSION_KEY in request.session:
        lang = request.session[translation.LANGUAGE_SESSION_KEY]
    return {'sw_version': sw_version,
            'sw_version_date': sw_version_date,
            'is_test_instance': is_test_instance,
            'flower_host': flower_server, 'flower_port': flower_port, 'flower_path': flower_path}
