#!/usr/bin/env python
# coding=UTF-8
__author__ = "Sven Schlarb"
__copyright__ = "Copyright 2016, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"
import os
import sys
import shutil
import tarfile
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.configuration import root_dir
from earkcore.metadata.mets.metsgenerator import MetsGenerator
from earkcore.metadata.premis.premisgenerator import PremisGenerator
from earkcore.packaging.unzip import Unzip
from earkcore.utils.xmlutils import rewrite_pretty_xml
from sandbox.sipgenerator.sipgenerator import SIPGenerator
from earkcore.utils.scripthelper import success
from earkcore.utils.scripthelper import failure
from earkcore.utils.scripthelper import print_headline
from earkcore.utils.fileutils import sub_dirs


def verify_file_created(file_type, file_path):
    if os.path.exists(file_path):
        success("%s file created successfully: %s" % (file_type, file_path))
    else:
        failure("Error creating %s file: %s" % (file_type, file_path))


def create_folder(package_folder):
    os.makedirs(package_folder)
    if os.path.exists(package_folder):
        success("Folder created in target directory: %s" % package_folder)
    else:
        failure("Failed creating package folder: %s" % package_folder)


def copy_folder(src, dest):
    _, leaf_folder = os.path.split(src)
    shutil.copytree(src, os.path.join(dest, leaf_folder))
    if os.path.exists(dest):
        success("Folder \"%s\" copied to target directory: \"%s\"" % (src, dest))
    else:
        failure("Failed copying folder \"%s\" to \"%s\"" % (src, dest))


def generate_representation_mets_files(package_path, package_name):
    # generate mets for each representation in representations folder
    reps_path = os.path.join(package_path, 'representations')
    if not os.path.exists(reps_path):
        failure("Representation directory missing: %s\nPlease add a folder 'representations' to the corresponding representation folder" % reps_path)
    for name in os.listdir(reps_path):
        rep_path = os.path.join(reps_path, name)
        if os.path.isdir(rep_path):
            print "Operation: generating representation METS file of representation: %s" % name
            mets_data = {'packageid': package_name,
                         'type': 'SIP',
                         'schemas': os.path.join(rep_path, 'schemas'),
                         'parent': ''}
            metsgen = MetsGenerator(rep_path)
            metsgen.createMets(mets_data)
            verify_file_created("Representation METS", os.path.join(rep_path, 'METS.xml'))
        else:
            failure("Not a representation directory: %s" % rep_path)


def process_package_folder(parent_dir, package_name, parent_id=None):
    print_headline("Package name: %s" % package_name)
    print "Parameter: parent directory: %s" % parent_dir
    print "Parameter: parent identifier: %s" % parent_id
    package_folder = os.path.join(ResultDirectory, package_name)
    create_folder(package_folder)
    subdirs = sub_dirs(os.path.join(parent_dir, package_name))
    representations = []
    for subdir in subdirs:
        if subdir in SipDirs:
            src = os.path.join(parent_dir, package_name, subdir)
            dest = os.path.join(ResultDirectory, package_name)
            print "Operation: copying SIP directory \"%s\" to target directory: %s" % (src, dest)
            copy_folder(src, dest)
        else:
            representations.append(subdir)
    print "Representations: %s" % representations

    print "Operation: creating METS for package \"%s\" at \"%s\"" % (package_name, os.path.join(ResultDirectory, package_name, "METS.xml"))
    if parent_id:
        print "Operation: append child node \"%s\" to parent node \"%s\" in METS of parent node  \"%s\"" % \
              (package_name, parent_id, os.path.join(ResultDirectory, parent_id, "METS.xml"))

    for subdir in subdirs:
        if subdir not in SipDirs:
            process_package_folder(os.path.join(parent_dir, package_name), subdir, package_name)

    package_path = os.path.join(ResultDirectory, package_name)

    generate_representation_mets_files(package_path, package_name)

    # generate package mets
    print "Operation: generating package METS file for package: %s" % package_name
    mets_data = {'packageid': package_name,
                 'type': 'SIP',
                 'schemas': os.path.join(package_path, 'schemas'),
                 'parent': ''}
    metsgen = MetsGenerator(package_path)
    metsgen.createMets(mets_data)
    mets_path = os.path.join(package_path, "METS.xml")
    verify_file_created("Package METS", mets_path)

    # Premis
    premis_md_folder = "metadata/preservation"
    create_folder(os.path.join(package_path, premis_md_folder))
    premisgen = PremisGenerator(package_path)
    premisgen.createPremis()
    info = {
        "outcome": "success",
        "task_name": "earkweb",
        "event_type": "SIP_CREATION",
        "linked_object": premisgen.addObject(mets_path)
    }
    premis_file_path = os.path.join(package_path, "metadata/preservation/premis.xml")
    premisgen.addEvent(premis_file_path, info)
    rewrite_pretty_xml(premis_file_path)
    verify_file_created("PREMIS", premis_file_path)

    # add child relationships to parent mets if any
    if len(representations) > 0:
        for rep in representations:
            print "Operation: adding child relationship: %s" % rep
            metsgen.addChildRelation(rep)

    # set parent relationship if existing
    if parent_id:
        print "Operation: setting parent relationship to parent id: %s" % parent_id
        metsgen.setParentRelation(parent_id)


def package_sips(sip_creation_working_dir):
    sip_dirs = sub_dirs(sip_creation_working_dir)
    print "Operation: packaging %d SIPs generated in the result directory" % len(sip_dirs)
    for sip_dir in sip_dirs:
        print_headline("Operation: packaging SIP folder: %s" % sip_dir)
        storage_tar_file = os.path.join(sip_creation_working_dir, sip_dir + '.tar')
        print "Operation: TAR package file \"%s\"" % storage_tar_file
        tar = tarfile.open(storage_tar_file, "w:")
        task_context_path = os.path.join(sip_creation_working_dir, sip_dir)
        for subdir, dirs, files in os.walk(task_context_path):
            for d in dirs:
                entry = os.path.join(subdir, d)
                if not os.listdir(entry):
                    tar.add(entry, arcname=os.path.relpath(entry, task_context_path))
            for f in files:
                entry = os.path.join(subdir, f)
                tar.add(entry, arcname=os.path.relpath(entry, task_context_path))
        tar.close()
        sipgen = SIPGenerator(sip_creation_working_dir)
        delivery_mets_file = os.path.join(sip_creation_working_dir, sip_dir + '.xml')
        sipgen.createDeliveryMets(storage_tar_file, delivery_mets_file)
        verify_file_created("TAR", storage_tar_file)
        verify_file_created("Delivery XML", delivery_mets_file)


if __name__ == '__main__':

    # configuration parameters
    print_headline("Configuration")
    test_package = os.path.join(root_dir, "earkresources/db-sip-batch-test/IP.AVID.RA.18005.godfather.zip")
    working_dir = os.path.join(root_dir, "test-hsi-folder")
    RootPackageDirectory = os.path.join(working_dir, "IP.AVID.RA.18005.godfather")
    ResultDirectory = os.path.join(working_dir, "Result")
    SipDirs = ["metadata", "documentation", "schemas", "representations"]
    print "Root package directory: %s" % RootPackageDirectory
    print "Result directory: %s" % ResultDirectory
    print "SIP directories: %s" % SipDirs

    # prepare test execution
    print_headline("Test setup")
    # unpackage test data if it does not exist in the working directory
    if not os.path.exists(RootPackageDirectory):
        unzip = Unzip()
        unzip.extract_with_report(test_package, working_dir)
        print "Test package %s extracted to working directory %s" % (test_package, working_dir)
    # delete result directory
    if os.path.exists(ResultDirectory):
        shutil.rmtree(ResultDirectory)
        print "Existing result directory deleted: %s" % ResultDirectory
    # result directory must not exist
    if os.path.exists(ResultDirectory) and len(os.listdir(ResultDirectory)) > 0:
        failure("Error: destination directory is not empty.")
    # create result directory if it does not exist
    if not os.path.exists(ResultDirectory):
        os.makedirs(ResultDirectory)
        if os.path.exists(ResultDirectory):
            success("Target directory created: %s" % ResultDirectory)

    # start process on root folder
    print_headline("SIP generation")
    root_parent_dir, root_package_name = os.path.split(RootPackageDirectory)
    print "Start processing package %s using root folder: %s" % (root_package_name, root_parent_dir)
    process_package_folder(root_parent_dir, root_package_name)
    print_headline("Packaging")
    package_sips(ResultDirectory)
