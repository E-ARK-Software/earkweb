#!/usr/bin/env python
# coding=UTF-8
"""
Repository file system and frontend database synchronization
Note: Requires that both, the django frontend and the storage backend can access the storage area. It can therefore not be used in a distributed setup.
"""
import json
import logging

from eatb.storage.pairtreestorage import PairtreeStorage
from eatb.utils.fileutils import get_immediate_subdirectories
from eatb.utils.terminal import print_headline, success, warning
from pairtree import ObjectNotFoundException

logger = logging.getLogger("earkweb")
logger.setLevel(logging.INFO)

import os
import sys
from taskbackend.ip_state import IpState

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

from earkweb.models import InformationPackage
from config.configuration import config_path_storage
from config.configuration import config_path_work
from django.core.exceptions import ObjectDoesNotExist


def sync_ip_state(ip_state_info, ip_in):
    if "storage_dir" in ip_state_info:
        ip_in.storage_dir = ip_state_info["storage_dir"]
    if "version" in ip_state_info:
        ip_in.version = ip_state_info["version"]
    if "identifier" in ip_state_info:
        ip_in.identifier = ip_state_info["identifier"]
    if "last_change" in ip_state_info:
        ip_in.last_change = ip_state_info["last_change"]
    ip_in.save()


if __name__ == "__main__":
    ps = PairtreeStorage(config_path_storage)
    print_headline("Synchronize local repository storage with information packages table")
    print(
        "Checking if the list of packages (in their respective latest version) is registered in the information packages table of the frontend database.")
    p_list = ps.latest_version_ip_list()
    for p in p_list:
        print("Information package: %s" % p['id'])
        print("- Version: %s" % p['version'])
        print("- Storage path: %s" % os.path.join(config_path_storage, p['path']))
        try:
            ip = InformationPackage.objects.get(identifier=p['id'])
            ip.storage_dir = os.path.join(config_path_storage, str(p['path']))
            ip.save()
        except ObjectDoesNotExist:
            InformationPackage.objects.create(
                work_dir="",
                process_id="",
                identifier=p['id'],
                storage_dir=os.path.join(config_path_storage, p['path']),
                package_name="",
                version=0
            )
    print_headline("Check storage location references in information packages table")
    print("""Checking if the storage locations in the information packages table of the frontend database reference existing files or unset the value otherwise.
Note that the storage location value is also unset if the identifier has changed and the storage location value is therefore outdated.""")
    p_list_ids = map(lambda x: x['id'], p_list)
    ips = InformationPackage.objects.all()
    for ip in ips:
        if ip.storage_dir != '':
            if not os.path.exists(ip.storage_dir):
                warning("Unsetting storage_dir because the referenced object is not accessible: %s" % ip.identifier)
                ip.storage_dir = ''
                ip.save()
            try:
                ps.get_object_path(ip.identifier)
            except ValueError:
                warning("Unsetting storage_dir because the referenced object is not accessible: %s" % ip.identifier)
                ip.storage_dir = ''
                ip.save()
            except ObjectNotFoundException:
                warning("Object not found in storage (record is removed): %s" % ip.identifier)
                ip.delete()

    print_headline("Check if a process for each working directory exists")
    print(
        "Checking if each working directory has an information package process with the corresponding UUID or create it otherwise.")
    work_subdirectories = get_immediate_subdirectories(config_path_work)
    for work_subdirectory in work_subdirectories:
        print("Checking working directory: %s" % work_subdirectory)
        ip = None
        try:
            ip = InformationPackage.objects.get(process_id=work_subdirectory)
        except ObjectDoesNotExist:
            ip_work_dir = os.path.join(config_path_work, work_subdirectory)
            warning("Creating missing information package process for existing working directory: %s" % work_subdirectory)
            ip = InformationPackage.objects.create(
                work_dir=ip_work_dir,
                process_id=work_subdirectory,
                package_name="",
                version=0
            )
        if ip:
            ip_state_doc_path = os.path.join(config_path_work, work_subdirectory, "state.json")
            if os.path.exists(ip_state_doc_path):
                success("State information available (state.json)")
                ip_state_info = json.load(open(ip_state_doc_path))
                sync_ip_state(ip_state_info, ip)
            else:
                warning("Process directory has no state information")
    success("Repository synchronization finished.")
