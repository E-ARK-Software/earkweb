#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
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
context = {"uid": "00fd16fa-8ee9-4d45-8bb6-fb29ed1f5bc9", "package_name": "my.test.package.001", "org_nsid": "repo", "identifier": "urn:uuid:7f987cf4-d7a7-4c0e-b765-1d5f84a1be1e", "md_format": "METS", "is_update_task": "", "storage_file": "/var/data/repo/work/d49409a6-1b24-4b6a-a30f-442799c57a75/urn+uuid+1017cc9b-eaed-4064-947e-a07c752d3760.tar"}

#context = {"uid": "260acadf-dc37-43cc-a0c5-eaf2c374dacc", "package_name": "mysip", "identifier": "urn:uuid:33333333-3333-3333-3333-333333333333", "org_nsid": "eark"}
aip_indexing(json.dumps(context))
