#!/usr/bin/env python
# coding=UTF-8
"""
Repository file system and frontend database synchronization
"""
import json
import logging
import os
import sys

from eatb.pairtree_storage import PairtreeStorage
from eatb.utils.fileutils import get_immediate_subdirectories
from eatb.utils.terminal import print_headline, success, warning
from pairtree import ObjectNotFoundException

logger = logging.getLogger("earkweb")
logger.setLevel(logging.INFO)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from earkweb.models import InformationPackage, Representation
from config.configuration import config_path_storage, config_path_work
from django.core.exceptions import ObjectDoesNotExist


def sync_ip_state(ip_state_info, ip_in):
    """Synchronize state information from state.json."""
    if "storage_dir" in ip_state_info:
        ip_in.storage_dir = ip_state_info["storage_dir"]
    if "version" in ip_state_info:
        ip_in.version = ip_state_info["version"]
    if "identifier" in ip_state_info:
        ip_in.identifier = ip_state_info["identifier"]
    if "last_change" in ip_state_info:
        ip_in.last_change = ip_state_info["last_change"]
    ip_in.save()


def store_metadata(ip, metadata_path):
    """Read metadata.json and store its content in InformationPackage fields."""
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_content = json.load(f)
        
        # Set InformationPackage fields from metadata
        ip.package_name = metadata_content.get("packageName", "").strip()
        ip.identifier = metadata_content.get("uid", ip.identifier)
        ip.external_id = metadata_content.get("externalId", "")
        ip.title = metadata_content.get("title", "")
        ip.content_information_type = metadata_content.get("contentInformationType", "")
        ip.content_category = metadata_content.get("contentCategory", "")
        ip.description = metadata_content.get("description", "")
        ip.original_creation_date = metadata_content.get("originalCreationDate", "")
        ip.tags = json.dumps(metadata_content.get("tags", []))  # Store as JSON string
        ip.linked_data = json.dumps(metadata_content.get("linkedData", []))  # Store as JSON string
        ip.locations = json.dumps(metadata_content.get("locations", []))  # Store as JSON string
        ip.contact_point = metadata_content.get("contactPoint", "")
        ip.contact_email = metadata_content.get("contactEmail", "")
        ip.publisher = metadata_content.get("publisher", "")
        ip.publisher_email = metadata_content.get("publisherEmail", "")
        ip.language = metadata_content.get("language", "")
        ip.created = metadata_content.get("created", "")
        ip.last_change = metadata_content.get("lastChange", "")
        
        # Store full metadata JSON
        ip.basic_metadata = json.dumps(metadata_content)

        ip.save()
        success(f"Stored metadata for {ip.identifier} (Package Name: {ip.package_name})")
    except Exception as e:
        warning(f"Failed to store metadata.json for {ip.identifier}: {e}")


def register_representations(ip, metadata_content):
    """Register representations based on the metadata.json content."""
    representations = metadata_content.get("representations", {})

    for rep_id, rep_data in representations.items():
        identifier = rep_id
        label = rep_data.get("distribution_label", "Unknown")
        description = rep_data.get("distribution_description", "")
        access_rights = rep_data.get("access_rights", "")
        file_metadata = json.dumps(rep_data.get("file_metadata", {}))  # Store as JSON
        
        # Create or update the Representation record
        representation, created = Representation.objects.get_or_create(
            identifier=identifier,
            ip=ip,
            defaults={
                "label": label,
                "description": description,
                "accessRights": access_rights,
                "file_metadata": file_metadata
            }
        )

        if created:
            success(f"Registered new representation: {identifier}")
        else:
            warning(f"Representation already exists: {identifier}")


if __name__ == "__main__":
    ps = PairtreeStorage(config_path_storage)

    print_headline("Synchronize local repository storage with information packages table")
    
    p_list = ps.latest_version_ip_list()
    for p in p_list:
        print(f"Information package: {p['id']}")
        print(f"- Version: {p['version']}")
        print(f"- Storage path: {os.path.join(config_path_storage, p['path'])}")
        
        try:
            ip = InformationPackage.objects.get(identifier=p['id'])
            ip.storage_dir = os.path.join(config_path_storage, str(p['path']))
            ip.save()
        except ObjectDoesNotExist:
            ip = InformationPackage.objects.create(
                work_dir="",
                uid="",
                identifier=p['id'],
                storage_dir=os.path.join(config_path_storage, p['path']),
                package_name="",
                version=0
            )

    print_headline("Check storage location references in information packages table")

    ips = InformationPackage.objects.all()
    
    for ip in ips:
        if ip.storage_dir != '':
            if not os.path.exists(ip.storage_dir):
                warning(f"Unsetting storage_dir because the referenced object is not accessible: {ip.identifier}")
                ip.storage_dir = ''
                ip.save()
            try:
                ps.get_object_path(ip.identifier)
            except (ValueError, ObjectNotFoundException):
                warning(f"Unsetting storage_dir because the referenced object is not accessible: {ip.identifier}")
                ip.storage_dir = ''
                ip.save()

    print_headline("Check if a process for each working directory exists")
    
    work_subdirectories = get_immediate_subdirectories(config_path_work)
    
    for work_subdirectory in work_subdirectories:
        print(f"Checking working directory: {work_subdirectory}")
        ip = None
        ip_work_dir = os.path.join(config_path_work, work_subdirectory)
        
        try:
            ip = InformationPackage.objects.get(uid=work_subdirectory)
        except ObjectDoesNotExist:
            warning(f"Creating missing information package process for existing working directory: {work_subdirectory}")
            ip = InformationPackage.objects.create(
                work_dir=ip_work_dir,
                uid=work_subdirectory,
                package_name="",
                version=0
            )
        
        # Store metadata.json content and set package_name if available
        metadata_path = os.path.join(ip_work_dir, "metadata/metadata.json")
        if os.path.exists(metadata_path):
            store_metadata(ip, metadata_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_content = json.load(f)
            register_representations(ip, metadata_content)
        else:
            warning(f"Process directory has no metadata.json: {work_subdirectory}")
        
    success("Repository synchronization finished.")
