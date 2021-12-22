import datetime
import os, sys

import requests
from eatb.utils.datetime import date_format

from config.configuration import django_service_protocol, django_service_host, django_service_port, backend_api_key, \
    verify_certificate

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

patch_data = {
        "identifier": "xyz",
        "version": int(22),
        "storage_dir": "/test/test/test",
        "last_change": date_format(datetime.datetime.utcnow()),
}

url = "%s://%s:%s/earkweb/api/ips/%s/" % (
    django_service_protocol, django_service_host, django_service_port, "cd9e6ee8-dfb3-48c4-834c-85d1cfb707b9")
response = requests.patch(url, data=patch_data, headers={'Authorization': 'Api-Key %s' % backend_api_key}, verify=verify_certificate)
print("Status information updated: %s (%d)" % (response.text, response.status_code))
