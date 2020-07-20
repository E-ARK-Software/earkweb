#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime

from eatb.utils.datetime import date_format, DT_ISO_FORMAT
from eatb.utils.fileutils import read_file_content

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()


from taskbackend.tasks import validate_working_directory
from taskbackend.tasks import create_manifest
from taskbackend.tasks import create_archival_package
from taskbackend.tasks import store_archival_package
from taskbackend.tasks import video_to_wav
from taskbackend.tasks import wav_to_classes
from taskbackend.tasks import process_audio_event_extraction_pipeline


#context = {"process_id": "bee115c0-bb0f-4d80-9b53-f6a735c6be95", "org_nsid": "repo"}
#context = {"process_id": "cd9e6ee8-dfb3-48c4-834c-85d1cfb707b9", "package_name": "testpackage.001",
#           "org_nsid": "repo", "identifier": "repo:hkdzkvqmmbtjksommahekeidmhifkqaffoffdesg", "md_format": "METS"}

#context = {"process_id": "cd9e6ee8-dfb3-48c4-834c-85d1cfb707b9",
#           "identifier": "repo:cmchfbsurejmrfyjevhcsfhxinaijwxnjmpixrzl",
#           "package_name": "testpackage.001", "org_nsid": "repo"}
#create_archival_package(json.dumps(context))


#result = video_to_wav("/home/schlarbs/test/", "/home/schlarbs/test/", "/home/schlarbs/test/car-parade.mp4")
result = wav_to_classes("/home/schlarbs/test/car-parade.mp4.wav")






