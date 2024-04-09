#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from taskbackend.tasks import sip_package
from taskbackend.tasks import validate_working_directory
from taskbackend.tasks import descriptive_metadata_validation
from taskbackend.tasks import aip_migrations
from taskbackend.tasks import aip_package_structure
from taskbackend.tasks import create_manifest
#from taskbackend.tasks import package_original_sip
from taskbackend.tasks import store_original_sip
from taskbackend.tasks import store_aip
from taskbackend.tasks import aip_indexing
from taskbackend.tasks import aip_packaging
from taskbackend.tasks import aip_record_events


context = {"uid": "dfe6ace2-7180-4f70-bd8c-aea88ee7d7ca", "identifier": "urn:uuid:ce64bc1e-a4d0-4a8d-abad-263d2e656793", "package_name": "mona.lisa.001", "org_nsid": "earkweb"}


#sip_package(json.dumps(context))

#store_original_sip(json.dumps(context))

aip_record_events(json.dumps(context))

#aip_package_structure(json.dumps(context))

#aip_package(json.dumps(context))

#store_aip(json.dumps(context))

#aip_indexing(json.dumps(context))



