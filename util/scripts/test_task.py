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
from taskbackend.tasks import prepare_sip_for_archiving
from taskbackend.tasks import aip_migrations
from taskbackend.tasks import aip_descriptive_metadata_validation
from taskbackend.tasks import aip_package_mets_creation
from taskbackend.tasks import create_manifest
from taskbackend.tasks import aip_packaging
from taskbackend.tasks import store_aip
from taskbackend.tasks import aip_indexing


#context = {"process_id": "bee115c0-bb0f-4d80-9b53-f6a735c6be95", "org_nsid": "eark"}
#context = {"process_id": "cd9e6ee8-dfb3-48c4-834c-85d1cfb707b9", "package_name": "testpackage.001",
#           "org_nsid": "eark", "identifier": "eark:hkdzkvqmmbtjksommahekeidmhifkqaffoffdesg", "md_format": "METS"}

context = {"process_id": "cd9e6ee8-dfb3-48c4-834c-85d1cfb707b9",
           "identifier": "eark:cmchfbsurejmrfyjevhcsfhxinaijwxnjmpixrzl",
           "package_name": "testpackage.001", "org_nsid": "eark"}
aip_packaging(json.dumps(context))
