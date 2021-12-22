#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()


from taskbackend.tasks import validate_working_directory
from taskbackend.tasks import descriptive_metadata_validation
from taskbackend.tasks import aip_migrations
from taskbackend.tasks import aip_package_mets_creation
from taskbackend.tasks import create_manifest
#from taskbackend.tasks import package_original_sip
from taskbackend.tasks import store_original_sip
from taskbackend.tasks import store_aip
from taskbackend.tasks import aip_indexing


#context = {"uid": "bee115c0-bb0f-4d80-9b53-f6a735c6be95", "org_nsid": "eark"}
#context = {"uid": "cd9e6ee8-dfb3-48c4-834c-85d1cfb707b9", "package_name": "testpackage.001",
#           "org_nsid": "eark", "identifier": "eark:hkdzkvqmmbtjksommahekeidmhifkqaffoffdesg", "md_format": "METS"}

#context = {"uid": "3b233728-898f-41fa-8a00-106ec9d4cf5a",
#           "identifier": "urn:uuid:3c7230dc-4bbc-4584-af9c-a9db5a99c49e",
#           "package_name": "test1234578", "org_nsid": "eark"}


#context = {"uid": "260acadf-dc37-43cc-a0c5-eaf2c374dacc", "package_name": "mysip", "identifier": "urn:uuid:33333333-3333-3333-3333-333333333333", "org_nsid": "eark"}
context = {"uid": "c6fd2048-4704-44ee-87a6-f8dc61a6441b", "package_name": "test", "identifier": "urn:uuid:bfe1ba12-6ce7-419c-9d29-50a0a3debb05"}
aip_indexing(json.dumps(context))
