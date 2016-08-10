#!/usr/bin/env python
# coding=UTF-8
"""
Repository file system and frontend database synchronization
Note: Requires the django frontend and the storage backend and can therefore not be used in a distributed setup.
Created on August 9, 2016

@author: Sven Schlarb
"""
import logging
logger = logging.getLogger("earkcore")
logger.setLevel(logging.INFO)

import os
import sys
from workers.ip_state import IpState

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

from earkcore.storage.pairtreestorage import PairtreeStorage
from earkcore.models import InformationPackage
from workflow.models import WorkflowModules
from config.configuration import config_path_storage
from config.configuration import config_path_work
from django.core.exceptions import ObjectDoesNotExist
from earkcore.utils.fileutils import get_immediate_subdirectories
from earkcore.utils.scripthelper import success
from earkcore.utils.scripthelper import warning
from earkcore.utils.scripthelper import print_headline


def sync_ip_state(ip_state_xml_in, ip_in):
    last_task_name = ip_state_xml_in.get_last_task()
    try:
        if last_task_name != ip_in.last_task_id:
            print "Syncing last task: %s" % last_task_name
            wf_module = WorkflowModules.objects.get(identifier=last_task_name)
            ip_in.last_task = wf_module
    except ObjectDoesNotExist:
        warning("Unable to sync last task, because the following task does not exist: %s" % last_task_name)
    state_persisted = ip_state_xml_in.get_state()
    state_in_db = ip_in.statusprocess
    if state_persisted != state_in_db:
        print "Syncing process status: %d" % ip_state_xml_in.get_state()
        ip_in.statusprocess = state_persisted
    ip_in.save()


if __name__ == "__main__":
    ps = PairtreeStorage(config_path_storage)
    print_headline("Synchronize local repository storage with information packages table")
    print "Checking if the list of packages (in their respective latest version) is registered in the information packages table of the frontend database."
    p_list = ps.latest_version_ip_list()
    for p in p_list:
        print "Information package: %s" % p['id']
        print "- Version: %s" % p['version']
        print "- Storage path: %s" % os.path.join(config_path_storage, p['path'])
        try:
            ip = InformationPackage.objects.get(identifier=p['id'])
            ip.storage_loc = os.path.join(config_path_storage, str(p['path']))
            ip.save()
        except ObjectDoesNotExist:
            InformationPackage.objects.create(
                path="",
                uuid="",
                identifier=p['id'],
                storage_loc=os.path.join(config_path_storage, p['path']),
                statusprocess=0,
                packagename="",
                last_task=WorkflowModules.objects.get(identifier="IPClose")
            )
    #
    #
    print_headline("Check storage location references in information packages table")
    print """Checking if the storage locations in the information packages table of the frontend database reference existing files or unset the value otherwise.
Note that the storage location value is also unset if the identifier has changed and the storage location value is therefore outdated."""
    p_list_ids = map(lambda x: x['id'], p_list)
    ips = InformationPackage.objects.all()
    for ip in ips:
        if ip.storage_loc != '':
            if not os.path.exists(ip.storage_loc):
                warning("Unsetting storage_loc because the referenced object is not accessible: %s" % ip.identifier)
                ip.storage_loc = ''
                ip.save()
            try:
                ps.get_object_path(ip.identifier)
            except ValueError:
                warning("Unsetting storage_loc because the referenced object is not accessible: %s" % ip.identifier)
                ip.storage_loc = ''
                ip.save()
    print_headline("Check if a process for each working directory exists")
    print "Checking if each working directory has an information package process with the corresponding UUID or create it otherwise."
    work_subdirectories = get_immediate_subdirectories(config_path_work)
    for work_subdirectory in work_subdirectories:
        print "Checking working directory: %s" % work_subdirectory
        ip = None
        try:
            ip = InformationPackage.objects.get(uuid=work_subdirectory)
        except ObjectDoesNotExist:
            ip_work_dir = os.path.join(config_path_work, work_subdirectory)
            warning("Creating missing information package process for existing working directory: %s" % work_subdirectory)
            ip = InformationPackage.objects.create(
                path=ip_work_dir,
                uuid=work_subdirectory,
                statusprocess=0,
                packagename="",
                last_task=WorkflowModules.objects.get(identifier="IPClose")
            )
        if ip:
            ip_state_doc_path = os.path.join(config_path_work, work_subdirectory, "state.xml")
            if os.path.exists(ip_state_doc_path):
                success("State information available (state.xml)")
                ip_state_xml = IpState.from_path(ip_state_doc_path)
                sync_ip_state(ip_state_xml, ip)
            else:
                warning("Process directory has no state information")
    success("Repository synchronization finished.")
