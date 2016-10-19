import logging
import os
import shutil
import sys
import time
import traceback
from functools import partial
from StringIO import StringIO
from os import walk
import urllib2

from celery import current_task
from earkcore.conversion.peripleo.pelagios_convert import PeripleoGmlProcessing
from earkcore.filesystem.informationpackage import get_last_submission_path, get_first_ip_path
from earkcore.rest.restclient import RestClient
from earkcore.utils.randomutils import randomword

from earkcore.utils.stringutils import multiple_replace
from workers.ip_state import IpState

logger = logging.getLogger(__name__)

from config.configuration import mets_schema_file, metadata_file_pattern_ead
from config.configuration import root_dir
from config.configuration import config_path_work
from config.configuration import siard_dbptk, siard_db_type, siard_db_host, siard_db_user, siard_db_passwd

from earkcore.filesystem.chunked import FileBinaryDataChunks
from earkcore.filesystem.fsinfo import fsize
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm
from earkcore.fixity.ChecksumFile import ChecksumFile
from earkcore.fixity.ChecksumValidation import ChecksumValidation
from earkcore.fixity.tasklib import check_transfer
from earkcore.metadata.mets.MetsValidation import MetsValidation
from earkcore.metadata.mets.ParsedMets import ParsedMets
from earkcore.metadata.mets.metsgenerator import MetsGenerator
from earkcore.metadata.premis.PremisManipulate import Premis
from earkcore.metadata.premis.premisgenerator import PremisGenerator
from earkcore.models import InformationPackage
from earkcore.packaging.untar import Untar
from earkcore.packaging.extract import Extract
from earkcore.packaging.task_utils import get_deliveries
from earkcore.rest.hdfsrestclient import HDFSRestClient
from earkcore.rest.restendpoint import RestEndpoint
from earkcore.search.solrclient import SolrClient
from earkcore.search.solrquery import SolrQuery
from earkcore.search.solrserver import SolrServer
from earkcore.storage.pairtreestorage import PairtreeStorage
from earkcore.utils import fileutils
from earkcore.utils import randomutils
from earkcore.utils.fileutils import mkdir_p, read_file_content, delete_directory_content, sub_dirs
from earkcore.utils.fileutils import remove_fs_item
from earkcore.utils.fileutils import remove_protocol
from earkcore.xml.deliveryvalidation import DeliveryValidation
from earkcore.metadata.task_utils import validate_ead_metadata, validate_gml_data
from earkweb.celeryapp import app
from sandbox.sipgenerator.sipgenerator import SIPGenerator
from tasklogger import TaskLogger
from workers.default_task import DefaultTask
from earkcore.metadata.XmlHelper import q
import uuid
from earkcore.utils.datetimeutils import current_timestamp, LengthBasedDateFormat
from lxml import etree, objectify
import fnmatch
from workers.default_task_context import DefaultTaskContext
from earkcore.format.formatidentification import FormatIdentification
from earkcore.process.cli.CliCommand import CliCommand
import subprocess32
from earkcore.filesystem.fsinfo import path_to_dict
from celery.exceptions import SoftTimeLimitExceeded
from config.configuration import hdfs_upload_service_ip, hdfs_upload_service_port
from config.configuration import hdfs_upload_service_endpoint_path, hdfs_upload_service_resource_path
import requests
from workers.concurrent_task import ConcurrentTask
from earkcore.utils.datetimeutils import ts_date
from earkcore.utils.pathutils import strip_prefixes
from earkcore.utils.pathutils import backup_file_path
from nltk.tag import StanfordNERTagger
from nltk import word_tokenize
from config.configuration import stanford_ner_models, stanford_jar, text_category_models, config_path_nlp, nlp_storage_path
from workers.dmhelpers.createarchive import CreateNLPArchive
import tarfile
from earkcore.metadata.ead.parsedead import ParsedEad
from earkcore.metadata.ead.parsedead import field_namevalue_pairs_per_file

from earkcore.utils.solrutils import SolrUtility
import re
import json

def custom_progress_reporter(task, percent):
    task.update_state(state='PROGRESS', meta={'process_percent': percent})

def init_task(pk_id, task_name, task_logfile_name):
    start_time = time.time()
    ip = InformationPackage.objects.get(pk=pk_id)
    if not ip.uuid:
        ip.uuid = randomutils.getUniqueID()
    ip_work_dir = os.path.join(config_path_work, ip.uuid)
    task_log_file_dir = os.path.join(ip_work_dir, 'metadata')
    task_log_file = os.path.join(task_log_file_dir, "%s.log" % task_logfile_name)
    # create working directory
    if not os.path.exists(ip_work_dir):
        os.mkdir(ip_work_dir)
    # create log directory
    if not os.path.exists(task_log_file_dir):
        os.mkdir(task_log_file_dir)
    # create PREMIS file or return handle to task
    if os.path.isfile(task_log_file_dir + '/PREMIS.xml'):
        with open(task_log_file_dir + '/PREMIS.xml', 'rw') as premis_file:
            package_premis_file = Premis(premis_file)
    elif not os.path.isfile(task_log_file_dir + '/PREMIS.xml'):
        premis_skeleton_file = root_dir + '/earkresources/PREMIS_skeleton.xml'
        with open(premis_skeleton_file, 'r') as premis_file:
            package_premis_file = Premis(premis_file)
        package_premis_file.add_agent('eark-aip-creation')
    tl = TaskLogger(task_log_file)
    tl.addinfo(("%s task %s" % (task_name, current_task.request.id)))
    return ip, ip_work_dir, tl, start_time, package_premis_file

def init_task2(ip_work_dir, task_name, task_logfile_name):
    start_time = time.time()
    # create working directory
    if not os.path.exists(ip_work_dir):
        os.mkdir(ip_work_dir)
    metadata_dir = os.path.join(ip_work_dir, 'metadata')
    task_log_file = os.path.join(metadata_dir, "%s.log" % task_logfile_name)
    # create log directory
    if not os.path.exists(metadata_dir):
        os.mkdir(metadata_dir)
    # create PREMIS file or return handle to task
    if os.path.isfile(metadata_dir + '/PREMIS.xml'):
        with open(metadata_dir + '/PREMIS.xml', 'rw') as premis_file:
            package_premis_file = Premis(premis_file)
    elif not os.path.isfile(metadata_dir + '/PREMIS.xml'):
        premis_skeleton_file = root_dir + '/earkresources/PREMIS_skeleton.xml'
        with open(premis_skeleton_file, 'r') as premis_file:
            package_premis_file = Premis(premis_file)
        package_premis_file.add_agent('eark-aip-creation')
    tl = TaskLogger(task_log_file)
    tl.addinfo(("%s task %s" % (task_name, current_task.request.id)))
    return tl, start_time, package_premis_file

import glob
def getDeliveryFiles(context_path):
    xml_files = glob.glob("%s/*.xml" % context_path)
    #print xml_files
    for delivery_xml in xml_files:
        sdv = DeliveryValidation()
        file_elements = sdv.getFileElements(context_path, delivery_xml, mets_schema_file)
        if file_elements:
            return file_elements, delivery_xml
    return None, None


@app.task(bind=True)
def SIPResetF(self, params):
    c = SIPReset()

    print "PATH: %s" % params['path']
    print "UUID: %s" % params['uuid']

    c.run(params['uuid'], params['path'], params['additional_data'])
    return params

@app.task(bind=True)
def extract_and_remove_package(self, package_file_path, target_directory, proc_logfile):
    tl = TaskLogger(proc_logfile)
    extr = Untar()
    proc_res = extr.extract(package_file_path, target_directory)
    if proc_res.success:
        tl.addinfo("Package %s extracted to %s" % (package_file_path, target_directory))
    else:
        tl.adderr("An error occurred while trying to extract package %s extracted to %s" % (package_file_path, target_directory))
    # delete file after extraction
    os.remove(package_file_path)
    return proc_res.success


@app.task(bind=True)
def ip_save_metadata_file(self, uuid, ip_file_path, content):
    tl = TaskLogger(os.path.join(config_path_work, uuid, "metadata/earkweb.log"))

    xml_file_path = ip_file_path
    if ip_file_path.startswith("submission"):
        xml_file_path = os.path.join('metadata', ip_file_path)
        # adapting paths for new storage location
        replacements = (u"/schema/ ../../schemas/", u"/schema/ ../../../../submission/schemas/"), \
                       (u"file:../../representations/", u"file:../../../../submission/representations/")
        content = multiple_replace(content, *replacements)
        logger.debug("Storing file in overruling path: %s" % xml_file_path)
    else:
        logger.debug("Writing file in path: %s" % xml_file_path)

    md_path, _ = os.path.split(xml_file_path)
    logger.debug("Creating folder to store metadata file: %s" % md_path)
    mkdir_p(os.path.join(config_path_work, uuid, md_path))

    abs_file_path = os.path.join(config_path_work, uuid, xml_file_path)

    if os.path.exists(abs_file_path):
        bf_path = backup_file_path(abs_file_path)
        shutil.copy(abs_file_path, bf_path)
        logger.debug("Backup copy of file created: %s" % bf_path)
    else:
        logger.debug("No backup file: %s" % xml_file_path)

    with open(abs_file_path, 'w') as ip_file:
        ip_file.write(content)
    ip_file.close()
    if read_file_content(abs_file_path) == content:
        success_msg = "File content successfully written to %s" % abs_file_path
        logger.debug(success_msg)
        tl.addinfo(success_msg)
        return True
    else:
        error_msg = "An error occurred while trying to write file: %s" % abs_file_path
        logger.debug(error_msg)
        tl.adderr(error_msg)
        return False

@app.task(bind=True)
def repo_working_dir_exists(self, uuid):
    from config.configuration import config_path_work
    working_dir = os.path.join(config_path_work, uuid)
    return os.path.exists(working_dir)

@app.task(bind=True)
def reception_dir_status(self, reception_d):
    from config.configuration import config_path_reception, config_path_work
    if not reception_d.startswith("/"):
        reception_d = "/%s" % reception_d
    allowed_dirs = config_path_reception, config_path_work
    if not reception_d.startswith(allowed_dirs):
        logger.error("Access to directory not permitted: %s" % reception_d)
        return {}
    logger.debug("Get information about directory: %s" % reception_d)
    return path_to_dict(reception_d)


@app.task(bind=True)
def set_process_state(self, uuid, valid):
    logger.debug("Set process state of process '%s' to '%s'." % (uuid, valid))
    ip_state_doc_path = os.path.join(config_path_work, uuid, "state.xml")
    if os.path.exists(ip_state_doc_path):
        ip_state_xml = IpState.from_path(ip_state_doc_path)
        ip_state_xml.set_state(0 if valid else 1)
        ip_state_xml.write_doc(ip_state_doc_path)
    return {'status': '0', "success": True}


@app.task(bind=True)
def create_ip_folder(self, *args, **kwargs):
    new_uuid = kwargs['uuid']
    from config.configuration import config_path_work
    target_folder = os.path.join(config_path_work, new_uuid)
    mkdir_p(target_folder)
    mkdir_p(os.path.join(target_folder, "representations"))
    mkdir_p(os.path.join(target_folder, "metadata"))
    logger.info("IP directory created: %s" % target_folder)


@app.task(bind=True)
def index_aip_storage(self, *args, **kwargs):
    # TODO: only index latest package version
    from config.configuration import local_solr_server_ip
    from config.configuration import local_solr_port
    from config.configuration import config_path_storage
    solr_server = SolrServer(local_solr_server_ip, local_solr_port)
    logger.info("Solr server base url: %s" % solr_server.get_base_url())
    sq = SolrQuery(solr_server)
    r = requests.get(sq.get_base_url())
    if not r.status_code == 200:
        logger.error("Solr server is not available at: %s" % sq.get_base_url())
        return
    else:
        logger.info("Using Solr server at: %s" % sq.get_base_url())
    # delete index first
    r = requests.get(sq.get_base_url() + "earkstorage/update?stream.body=%3Cdelete%3E%3Cquery%3E*%3C/query%3E%3C/delete%3E&commit=true")
    package_count = 0
    solr_client = SolrClient(solr_server, "earkstorage")
    for dirpath,_,filenames in os.walk(config_path_storage):
       for f in filenames:
           package_abs_path = os.path.abspath(os.path.join(dirpath, f))
           if package_abs_path.endswith(".tar"):
               logger.info("=========================================================")
               logger.info(package_abs_path)
               logger.info("=========================================================")
               _, file_name = os.path.split(package_abs_path)
               identifier = file_name[0:-4]
               results = solr_client.post_tar_file(package_abs_path, identifier)
               logger.info("Total number of files posted: %d" % len(results))
               num_ok = sum(1 for result in results if result['status'] == 200)
               logger.info("Number of files posted successfully: %d" % num_ok)
               num_failed = sum(1 for result in results if result['status'] != 200)
               logger.info( "Number of plain documents: %d" % num_failed)
               package_count += 1
    logger.info("Indexing of %d packages available in local storage finished" % package_count)


@app.task(bind=True)
def run_package_ingest(self, *args, **kwargs):
    package_file = kwargs['package_file']
    predef_id_mapping = kwargs['predef_id_mapping']
    logger.debug("predefined packagename-id mapping: %s" % predef_id_mapping)
    current_task.update_state(state='PENDING', meta={'package_file': package_file, 'last_task': "AIPReset"})
    from config.configuration import config_path_reception
    from earkcore.batch.import_sip import import_package
    try:
        task_context = import_package(current_task, os.path.join(config_path_reception, package_file), predef_id_mapping)
        #task_context = import_package(current_task, os.path.join(config_path_reception, package_file))
        if hasattr(task_context, 'task_status') and task_context.task_status == 0:
            os.remove(os.path.join(config_path_reception, package_file))
            p, _ = os.path.splitext(os.path.join(config_path_reception, package_file))
            delivery_xml = "%s.xml" % p
            if os.path.exists(delivery_xml):
                os.remove(delivery_xml)
            return { 'package_file': package_file, 'storage_loc': task_context.additional_data['storage_loc'], 'status': task_context.task_status, "success": True}
        else:
            current_task.update_state(state='FAILURE', meta={'package_file': package_file})
            return { 'package_file': package_file, 'storage_loc': "", 'status': "1", "success": False, "errmsg": "Import workflow failed."}
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        current_task.update_state(state='FAILURE', meta={'package_file': package_file})
        return { 'package_file': package_file, 'storage_loc': "", 'status': "1", "success": False, "errmsg": err.message}


@app.task(bind=True)
def run_sipcreation_batch(self, *args, **kwargs):
    uuid = kwargs['uuid']
    packagename = kwargs['packagename']
    path = kwargs['path']
    if not uuid or not packagename or not path:
        raise ValueError("Required parameters: uuid, packagename, path")
    from config.configuration import config_path_reception
    from earkcore.utils.fileutils import secure_copy_tree
    if path.startswith(config_path_reception) and path.endswith(packagename):
        if secure_copy_tree(path, os.path.join(config_path_work, uuid)):
            shutil.rmtree(path)
        else:
            err_msg = "Error while copying IP '%s' data from the reception area." % packagename
            logger.error(err_msg)
            current_task.update_state(state='FAILURE', meta={'uuid': uuid})
            return {'uuid': uuid, 'status': "1", "success": False, "errmsg": err_msg}
    current_task.update_state(state='PENDING', meta={'uuid': uuid, 'last_task': "SIPReset"})
    from earkcore.batch.create_sip import create_sip
    try:
        task_context = create_sip(current_task, uuid, packagename)
        if hasattr(task_context, 'task_status') and task_context.task_status == 0:
            return { 'uuid': uuid, 'status': task_context.task_status, "success": True}
        else:
            current_task.update_state(state='FAILURE', meta={'uuid': uuid})
            return { 'uuid': uuid, 'status': "1", "success": False, "errmsg": "Import workflow failed."}
    except Exception, err:
        tb = traceback.format_exc()
        logging.error(str(tb))
        current_task.update_state(state='FAILURE', meta={'uuid': uuid})
        return { 'uuid': uuid, 'status': "1", "success": False, "errmsg": err.message}

class SIPReset(DefaultTask):

    accept_input_from = ['All']

    def run_task(self, task_context):
        """
        SIP Creation Reset run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Reset'

        # implementation
        task_context.task_status = 0
        task_context.additional_data['identifier'] = ""
        return task_context.additional_data


class SIPDescriptiveMetadataValidation(DefaultTask):

    accept_input_from = [SIPReset.__name__, 'SIPDescriptiveMetadataValidation']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:2,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Descriptive Metadata Validation'

        tl = task_context.task_logger
        metadata_dir = os.path.join(task_context.path, 'metadata/')
        tl.addinfo("Looking for EAD metadata files in metadata directory: %s" % metadata_dir)

        # "warning" state for validation errors
        try:
            md_files_valid = []
            from earkcore.utils.fileutils import find_files
            for filename in find_files(metadata_dir, metadata_file_pattern_ead):
                path, md_file = os.path.split(filename)
                tl.addinfo("Found EAD file '%s'" % md_file)
                md_files_valid.append(validate_ead_metadata(path, md_file, None, tl))
            if len(md_files_valid) == 0:
                tl.addinfo("No EAD metadata files found.")
            valid = False not in md_files_valid
            if valid:
                tl.addinfo("Descriptive metadata validation completed successfully.")
            task_context.task_status = 0 if valid else 2
        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2

        return task_context.additional_data


class SIPDicomValidation(DefaultTask):
    """
    Task requires module "dicom" (not installed by default):
    pip install pydicom==0.9.9
    """

    accept_input_from = [SIPReset.__name__, SIPDescriptiveMetadataValidation.__name__, 'SIPDicomValidation']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:6,type:0,stage:0
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Dicom Validation'

        tl = task_context.task_logger
        metadata_dir = os.path.join(task_context.path, 'representations/')
        tl.addinfo("Looking for Dicom image data directory: %s" % metadata_dir)

        # "warning" state for validation errors
        try:
            md_files_valid = []
            from earkcore.utils.fileutils import find_files
            for filename in find_files(metadata_dir, "*.dcm"):
                path, dicom_image_file = os.path.split(filename)
                tl.addinfo("Validating Dicom image file '%s'" % dicom_image_file)
                import dicom
                from dicom.errors import InvalidDicomError
                try:
                    df = dicom.read_file(filename)
                    tl.addinfo("Dicom image file rows %d" % int(df.Rows))
                    tl.addinfo("Dicom image file rows %d" % int(df.Columns))
                    tl.addinfo("%s" % df, False)
                    tech_md_dir = os.path.join(task_context.path, "metadata/technical")
                    mkdir_p(tech_md_dir)
                    tech_md_file = os.path.join(tech_md_dir, "%s.log" % dicom_image_file)
                    with open(tech_md_file, "w") as md_file:
                        md_file.write("%s" % df)
                    tl.addinfo("Dicom image '%s' validated successfully." % dicom_image_file)
                    md_files_valid.append(True)
                except InvalidDicomError as err:
                    tl.adderr('Invalid Dicom file %s: %s' % (dicom_image_file, err))
                    md_files_valid.append(False)
            if len(md_files_valid) == 0:
                tl.addinfo("No Dicom image data files found.")
            valid = False not in md_files_valid
            if valid:
                tl.addinfo("Dicom image files validated successfully.")
                task_context.task_status = 0
            else:
                tl.adderr("Warning: Dicom image file validation errors occurred.")
                task_context.task_status = 2
        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2

        return task_context.additional_data


class SIPPackageMetadataCreation(DefaultTask):

    # Descriptive metadata check can be skipped
    accept_input_from = [SIPReset.__name__, SIPDescriptiveMetadataValidation.__name__, SIPDicomValidation.__name__, 'SIPPackageMetadataCreation']

    def run_task(self, task_context):
        """
        SIP Package metadata creation run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:7,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Package Metadata Creation'

        reps_path = os.path.join(task_context.path, 'representations')
        for name in os.listdir(reps_path):
            rep_path = os.path.join(reps_path, name)
            if os.path.isdir(rep_path):
                # Premis
                premisgen = PremisGenerator(rep_path)
                premisgen.createPremis()
                # Mets
                mets_data = {'packageid': task_context.uuid,
                             'type': 'SIP',
                             'schemas': os.path.join(task_context.path, 'schemas'),
                             'parent': ''}
                metsgen = MetsGenerator(rep_path)
                metsgen.createMets(mets_data)

        #mets_files = []
        #for name in os.listdir(reps_path):
        #    rep_mets_path = os.path.join(reps_path, name, "METS.xml")
        #    if os.path.exists(rep_mets_path) and os.path.isfile(rep_mets_path):
        #        mets_files.append(rep_mets_path)

        # also, Premis
        premisgen = PremisGenerator(task_context.path)
        premisgen.createPremis()

        # create SIP parent Mets
        mets_data = {'packageid': task_context.uuid,
                     'type': 'SIP',
                     'schemas': os.path.join(task_context.path, 'schemas'),
                     'parent': ''}
        metsgen = MetsGenerator(task_context.path)
        metsgen.createMets(mets_data)

        task_context.task_status = 0
        return task_context.additional_data


class SIPPackaging(DefaultTask):

    accept_input_from = [SIPPackageMetadataCreation.__name__, 'SIPPackaging']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:8,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'N/A'

        task_context.task_logger.addinfo("Package name: %s" % task_context.additional_data['packagename'])
        tl = task_context.task_logger
        reload(sys)
        sys.setdefaultencoding('utf8')

        # append generation number to tar file; if tar file exists, the generation number is incremented
        storage_tar_file = os.path.join(task_context.path, task_context.additional_data['packagename']+ '.tar')
        tar = tarfile.open(storage_tar_file, "w:")
        tl.addinfo("Packaging working directory: %s" % task_context.path)
        total = sum([len(files) for (root, dirs, files) in walk(task_context.path)])
        tl.addinfo("Total number of files in working directory %d" % total)
        # log file is closed at this point because it will be included in the package,
        # subsequent log messages can only be shown in the gui

        i = 0
        for subdir, dirs, files in os.walk(task_context.path):

            for dir in dirs:
                entry = os.path.join(subdir, dir)
                if not os.listdir(entry):
                    tar.add(entry, arcname=os.path.relpath(entry, task_context.path))

            for file in files:
                entry = os.path.join(subdir, file)
                tar.add(entry, arcname=os.path.relpath(entry, task_context.path))
                if i % 10 == 0:
                    perc = (i * 100) / total
                    self.update_state(state='PROGRESS', meta={'process_percent': perc})
                i += 1
        tar.close()

        tl.log.append("Package stored: %s" % storage_tar_file)

        sipgen = SIPGenerator(task_context.path)
        delivery_mets_file = os.path.join(task_context.path, task_context.additional_data['packagename']+ '.xml')
        sipgen.createDeliveryMets(storage_tar_file, delivery_mets_file)
        tl.log.append("Delivery METS3 stored: %s" % delivery_mets_file)
        task_context.task_status = 0
        return task_context.additional_data


class SIPTransferToReception(DefaultTask):

    accept_input_from = [SIPPackaging.__name__, 'SIPTransferToReception']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:9,type:1,stage:0
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'N/A'

        task_context.task_logger.addinfo("Transfer package: %s" % task_context.additional_data['packagename'])
        tl = task_context.task_logger

        from config.configuration import config_path_reception
        #delete_directory_content(config_path_reception)

        tar_file_name = task_context.additional_data['packagename']+ '.tar'
        delivery_xml_file_name = task_context.additional_data['packagename']+ '.xml'
        storage_tar_file = os.path.join(task_context.path, tar_file_name)
        delivery_xml_file = os.path.join(task_context.path, delivery_xml_file_name)
        shutil.copy(storage_tar_file, os.path.join(config_path_reception, tar_file_name))
        shutil.copy(delivery_xml_file, os.path.join(config_path_reception, delivery_xml_file_name))

        task_context.task_status = 0
        return task_context.additional_data


class SIPClose(DefaultTask):

    accept_input_from = [SIPPackaging.__name__, SIPTransferToReception.__name__, 'SIPClose']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:10,type:1,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'N/A'

        task_context.task_logger.addinfo("Closing package: %s" % task_context.additional_data['packagename'])
        tl = task_context.task_logger

        def rem_dir(dirname):
            if dirname:
                dir = os.path.join(task_context.path, dirname)
                if os.path.exists(dir) and dir is not task_context.path:
                    shutil.rmtree(dir)
                task_context.task_logger.addinfo("Directory deleted: %s" % dir)

        # directories to be removed
        sip_dirs = ("representations", "metadata")
        for d in sip_dirs: rem_dir(d)

        task_context.task_status = 0
        return task_context.additional_data


class SIPtoAIPReset(DefaultTask):

    accept_input_from = ['All']

    def run_task(self, task_context, *args, **kwargs):
        """
        SIP to AIP Reset run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = "SIP to AIP Conversion Reset"

        # create working directory if it does not exist
        if not os.path.exists(task_context.path):
            fileutils.mkdir_p(task_context.path)

        # remove and recreate empty directories
        items_to_remove = ['METS.xml', 'submission', 'representations', 'schemas', 'metadata', 'Content', 'Metadata', 'IP.xml', 'earkweb']
        for item in items_to_remove:
            remove_fs_item(task_context.uuid, task_context.path, item)

        # remove extracted sips
        deliveries = get_deliveries(task_context.path, task_context.task_logger)
        for delivery in deliveries:
            if os.path.exists(os.path.join(task_context.path, str(delivery))):
                shutil.rmtree(os.path.join(task_context.path, str(delivery)))

        # create a brand-new Premis file and metadata dir, else DefaultTask raises an exception when trying to add an event!
        os.makedirs(os.path.join(task_context.path, 'metadata/preservation/'))
        path_premis = os.path.join(task_context.path, 'metadata/preservation/premis.xml')
        premisgen = PremisGenerator(task_context.path)
        premisgen.createPremis()
        task_context.package_premis = path_premis

        # success status
        task_context.task_status = 0
        task_context.additional_data['identifier'] = ""
        return task_context.additional_data


class SIPDeliveryValidation(DefaultTask):

    accept_input_from = [SIPtoAIPReset.__name__, SIPClose.__name__, "SIPDeliveryValidation"]

    def run_task(self, task_context):
        """
        SIP Delivery Validation run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:2,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Delivery Validation'

        # TODO: rework for new MetsValidation.py?

        tl = task_context.task_logger
        tl.addinfo("Marker %s" % task_context.path)
        file_elements, delivery_xml = getDeliveryFiles(task_context.path)

        if not file_elements:
            tl.addinfo("No valid delivery validation xml found. Aborting.")
            task_context.task_status = 1
            return task_context.additional_data

        # continue normally we have only one tar
        delivery_file = file_elements[0]
        tl.addinfo("Package file: %s" % delivery_file)
        tl.addinfo("Delivery XML file: %s" % delivery_xml)
        tl.addinfo("Schema file: %s" % mets_schema_file)

        # Checksum validation
        checksum_expected = ParsedMets.get_file_element_checksum(delivery_file)
        checksum_algorithm = ParsedMets.get_file_element_checksum_algorithm(delivery_file)
        file_reference = ParsedMets.get_file_element_reference(delivery_file)

        tl.addinfo("Extracted file reference: %s" % file_reference)
        file_path = os.path.join(task_context.path, remove_protocol(file_reference))
        tl.addinfo("Computing checksum for file: %s" % file_path)
        csval = ChecksumValidation()
        valid_checksum = csval.validate_checksum(file_path, checksum_expected, ChecksumAlgorithm.get(checksum_algorithm))
        #tl.append("Checksum validity: \"%s\"" % str(valid_checksum))
        if not valid_checksum:
            tl.adderr("Checksum of the SIP tar file is invalid.")
            task_context.task_status = 1
        else:
            tl.addinfo("Checksum is valid.")
            task_context.task_status = 0

        # we have a SIC (collection) so split delivery into subparts containing
        # individual SIPS (generate delivery xmls and tasks)
        # for file_element in file_elements:
        #     #split original mets in individual pieces
        #     #uuid = getUniqueID()
        #     #sip_directory = os.path.join(config_path_work, uuid)
        #
        #     sipgen = SIPGenerator(task_context.path)
        #     file_reference = file_element.get_file_element_reference()
        #     file_name = remove_protocol(file_reference)
        #     storage_tar_file = os.path.join(task_context.path, file_name)
        #     delivery_mets_file = os.path.join(task_context.path, os.path.basename(file_name)+ '.xml')
        #     sipgen.createDeliveryMets(storage_tar_file, delivery_mets_file)
        #     tl.log.append("Delivery METS stored: %s" % delivery_mets_file)


        # deliveries = get_deliveries(task_context.path, task_context.task_logger)
        # if len(deliveries) == 0:
        #     tl.adderr("No delivery found in working directory")
        #     task_context.task_status = 1
        # else:
        #     for delivery in deliveries:
        #         tar_file = deliveries[delivery]['tar_file']
        #         delivery_file = deliveries[delivery]['delivery_xml']
        #
        #         tl.addinfo("Package file: %s" % delivery_file)
        #         tl.addinfo("Delivery XML file: %s" % delivery_file)
        #         tl.addinfo("Schema file: %s" % mets_schema_file)
        #
        #         sdv = DeliveryValidation()
        #         validation_result = sdv.validate_delivery(task_context.path, delivery_file, schema_file, tar_file)
        #         tl.log = tl.log + validation_result.log
        #         tl.err = tl.err + validation_result.err
        #         tl.addinfo("Delivery validation result (xml/file size/checksum): %s" % validation_result.valid)
        #         if not validation_result.valid:
        #             tl.adderr("Delivery invalid: %s" % delivery)
        #             task_context.task_status = 1
        #         else:
        #             task_context.task_status = 0
        task_context.task_status = 0
        task_context.additional_data['identifier'] = ""
        return task_context.additional_data

#def getIdentifierFromIdentifierMap(task_context, packagename):
#    identifier_map = None
#    if 'identifier_map' in task_context.additional_data:
#        identifier_map = task_context.additional_data['identifier_map']

def getIdentifierMapFromContext(task_context):
    identifier_map = None
    if 'identifier_map' in task_context.additional_data:
        identifier_map = task_context.additional_data['identifier_map']
    return identifier_map

def getIdentifierForPackagename(identifier_map, package_name):
    identifier = None
    if package_name in identifier_map:
        identifier = identifier_map[package_name]
    return identifier


class IdentifierAssignment(DefaultTask):

    accept_input_from = [SIPDeliveryValidation.__name__, "IdentifierAssignment"]

    def run_task(self, task_context):
        """
        Identifier Assignment run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:3,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Identifier Assignment'

        tl = task_context.task_logger

        identifier_map = getIdentifierMapFromContext(task_context)

        identifier = None
        if identifier_map:
            packagename = task_context.additional_data['packagename']
            if packagename in identifier_map:
                identifier = identifier_map[packagename]
                tl.addinfo("Provided identifier assigned: %s" % identifier)
            else:
                tl.adderr("Cannot find uuid for package name %s in provided identifier_map" % packagename)
                task_context.task_status = 1
        else:
            identifier = "urn:uuid:%s" % randomutils.getUniqueID() #
            tl.addinfo("New identifier assigned: %s" % identifier)

        # Set identifier in METS
        try:
            mets_path = os.path.join(task_context.path, 'METS.xml')
            if os.path.isfile(mets_path):
                # If the Premis file exists, replace every events <linkingObjectIdentifierValue> with the new
                # identifier, as well as the <objectIdentifierValue> for the object resembling the package.
                parsed_mets = etree.parse(mets_path)
                root = parsed_mets.getroot()
                root.set('OBJID', 'urn:uuid:%s' % identifier)

                # write changed METS file
                mets_content = etree.tostring(parsed_mets, encoding='UTF-8', pretty_print=True, xml_declaration=True)
                with open(mets_path, 'w') as output_file:
                    output_file.write(mets_content)
                tl.addinfo("AIP identifier set in METS file.")
                task_context.task_status = 0
        except Exception, e:
            tl.adderr('An error ocurred when trying to update the METS file with the new identifier: %s' % str(e))
            tl.adderr(traceback.format_exc())
            task_context.task_status = 1
            return task_context.additional_data

        try:
            if os.path.isfile(os.path.join(task_context.path, 'metadata/preservation/premis.xml')):
                # If the Premis file exists, replace every events <linkingObjectIdentifierValue> with the new
                # identifier, as well as the <objectIdentifierValue> for the object resembling the package.
                premis_path = os.path.join(task_context.path, 'metadata/preservation/premis.xml')
                PREMIS_NS = 'info:lc/xmlns/premis-v2'
                parsed_premis = etree.parse(premis_path)

                object = parsed_premis.find(q(PREMIS_NS, 'object'))
                object_id_value = object.find('.//%s' % q(PREMIS_NS, 'objectIdentifierValue'))
                object_id_value.text = identifier

                events = parsed_premis.findall(q(PREMIS_NS, 'event'))
                for event in events:
                    event_rel_obj = event.find('.//%s' % q(PREMIS_NS, 'linkingObjectIdentifierValue'))
                    event_rel_obj.text = identifier

                # write the changed Premis file
                str = etree.tostring(parsed_premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
                with open(premis_path, 'w') as output_file:
                    output_file.write(str)

                task_context.task_status = 0
            else:
                tl.adderr('Can\'t find a Premis file to update it with new identifier!')
                task_context.task_status = 1
        except Exception, e:
            tl.adderr('An error ocurred when trying to update the Premis file with the new identifier: %s' % e)
            task_context.task_status = 1

        task_context.additional_data['identifier'] = identifier
        tl.addinfo('Assigned identifier %s' % identifier)
        return task_context.additional_data


class SIPExtraction(DefaultTask):

    accept_input_from = [IdentifierAssignment.__name__]

    def run_task(self, task_context):
        """
        SIP extraction
        @type       tc: task configuration line (used to insert read tl.addinfo("New identifier assigned: %s" % identifier)task properties in database table)
        @param      tc: order:4,type:2,stage:2
        """

        tl = task_context.task_logger

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Extraction'
        if not 'identifier' in task_context.additional_data:
            task_context.task_status = 1
            tl.adderr("Parameter 'identifier' is not defined in additional data!")
            return task_context.additional_data

        print 'identifier: %s' % task_context.additional_data['identifier']

        deliveries = get_deliveries(task_context.path, task_context.task_logger)
        if len(deliveries) == 0:
            tl.adderr("No delivery found in working directory")
            task_context.task_status = 0
        else:
            for delivery in deliveries:
                package_file = deliveries[delivery]['package_file']
                extr = Extract.factory(package_file)
                custom_reporter = partial(custom_progress_reporter, self)
                package_file_abs_path = os.path.join(task_context.path, package_file)
                target_folder = os.path.join(task_context.path, str(delivery)) if extr.has_member(package_file_abs_path, 'METS.xml') else task_context.path
                tl.addinfo("Extracting package file %s to %s" % (package_file_abs_path,target_folder))
                extr.extract_with_report(package_file_abs_path, target_folder, progress_reporter=custom_reporter)
            tl.log += extr.log
            tl.err += extr.err
            task_context.task_status = 0
        return task_context.additional_data


class SIPValidation(DefaultTask):

    accept_input_from = [SIPExtraction.__name__, "SIPValidation"]

    def run_task(self, task_context):
        """
        SIP Validation run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:5,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP Validation'

        tl = task_context.task_logger
        valid = True

        def item_exists(descr, item):
            if os.path.exists(item):
                tl.addinfo("%s found: %s" % (descr, os.path.abspath(item)))
                task_context.task_status = 0
                return True
            else:
                tl.adderr(("%s missing: %s" % (descr, os.path.abspath(item))))
                task_context.task_status = 1
                return False

        # working directory must contain an IP or the IP must be in a subfolder
        ip_path = get_first_ip_path(task_context.path)
        if not ip_path:
            tl.adderr("No information package found")
            task_context.task_status = 1
            return task_context.additional_data
        else:
            tl.addinfo("Information package folder: %s" % ip_path)

        # package METS file validation
        # root_mets_path = os.path.join(ip_path, "METS.xml")
        # root_mets_validator = MetsValidation(ip_path)
        # if root_mets_validator.validate_mets(root_mets_path):
        #     tl.addinfo("Information package METS file validated successfully: %s" % root_mets_path)
        # else:
        #     tl.adderr("Error validating package METS file: %s" % root_mets_path)
        #     for err in root_mets_validator.validation_errors:
        #         tl.adderr(str(err))
        #     valid = False

        # representations folder is mandatory
        representations_path = os.path.join(ip_path, "representations")
        if not item_exists("Representations folder", representations_path):
            return task_context.additional_data

        # representation METS file validation
        if os.path.exists(os.path.join(ip_path, "representations")):
            for name in os.listdir(representations_path):
                rep_path = os.path.join(representations_path, name)
                if os.path.isdir(rep_path):
                    mets_validator = MetsValidation(rep_path)
                    valid &= mets_validator.validate_mets(os.path.join(rep_path, 'METS.xml'))

        # IP is valid if all METS files are valid
        if valid:
            task_context.task_status = 0
        else:
            task_context.task_status = 1
            for error in mets_validator.validation_errors:
                tl.adderr(error)
        return task_context.additional_data


class SIPRestructuring(DefaultTask):

    accept_input_from = [SIPValidation.__name__, SIPExtraction.__name__]

    def run_task(self, task_context):
        """
        SIP Restructuring run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:6,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'SIP to AIP Restructuring'

        tl = task_context.task_logger
        deliveries = get_deliveries(task_context.path, task_context.task_logger)
        if len(deliveries) == 0:
            tl.adderr("No delivery found in working directory")
            task_context.task_status = 1
        else:
            for delivery in deliveries:
                tl.addinfo("Restructuring content of package: %s" % str(delivery))

                # TODO: maybe remove the state.xml already during SIP packaging
                delivery_path = os.path.join(task_context.path, str(delivery))
                state_xml_path = os.path.join(delivery_path, 'state.xml')
                if os.path.exists(state_xml_path):
                    os.remove(state_xml_path)

                fs_childs = os.listdir(str(delivery_path))
                for fs_child in fs_childs:
                    source_item = os.path.join(delivery_path, fs_child)
                    target_folder = os.path.join(task_context.path, "submission")
                    if not os.path.exists(target_folder):
                        os.mkdir(target_folder)
                    tl.addinfo("Move SIP folder '%s' to '%s" % (source_item, target_folder))
                    shutil.move(source_item, target_folder)
                os.removedirs(delivery_path)

            task_context.task_status = 0
        return task_context.additional_data


class AIPDescriptiveMetadataValidation(DefaultTask):

    accept_input_from = [SIPRestructuring.__name__, 'AIPDescriptiveMetadataValidation']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:7,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Descriptive Metadata Validation'

        tl = task_context.task_logger
        tl.addinfo("EAD metadata file validation.")

        submiss_dir = 'submission'
        md_dir = 'metadata'
        md_subdir_descr = 'descriptive'

        descriptive_md_dir = os.path.join(md_dir, md_subdir_descr)

        submiss_descr_md_dir = os.path.join(get_last_submission_path(task_context.path), descriptive_md_dir)

        overruling_metadata_dir = os.path.join(task_context.path, md_dir, submiss_dir, descriptive_md_dir)

        tl.addinfo("Looking for EAD metadata files in metadata directory: %s" % strip_prefixes(submiss_descr_md_dir, task_context.path))
        tl.addinfo("Overruling metadata directory: %s" % strip_prefixes(overruling_metadata_dir, task_context.path))

        # "warning" state for validation errors
        try:
            md_files_valid = []
            from earkcore.utils.fileutils import find_files
            for filename in find_files(submiss_descr_md_dir, metadata_file_pattern_ead):
                md_path, md_file = os.path.split(filename)
                tl.addinfo("Found descriptive metadata file in submission folder: '%s'" % md_file)
                tl.addinfo("Looking for overruling version in AIP metadata folder: '%s'" % strip_prefixes(overruling_metadata_dir, task_context.path))
                overruling_md_file = os.path.join(overruling_metadata_dir, md_file)
                validation_md_path = md_path
                if os.path.exists(overruling_md_file):
                    tl.addinfo("Overruling version of descriptive metadata file found: %s" % strip_prefixes(overruling_md_file, task_context.path))
                    validation_md_path = overruling_metadata_dir
                else:
                    tl.addinfo("No overruling version of descriptive metadata file in AIP metadata folder found.")
                md_files_valid.append(validate_ead_metadata(validation_md_path, md_file, None, tl))
            if len(md_files_valid) == 0:
                tl.addinfo("No descriptive metadata files found.")
            valid = False not in md_files_valid
            if valid:
                tl.addinfo("Descriptive metadata validation completed successfully.")
            task_context.task_status = 0 if valid else 2
        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2

        return task_context.additional_data


class AIPMigrations(DefaultTask):

    accept_input_from = [SIPRestructuring.__name__, AIPDescriptiveMetadataValidation.__name__, 'MigrationProcess', 'AIPMigrations', 'AIPCheckMigrationProgress']

    def run_task(self, task_context):
        """
        AIP File Migration
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:8,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Migrations'

        # make metadata/earkweb dir for temporary files
        if not os.path.exists(os.path.join(task_context.path, 'metadata/earkweb')):
            os.makedirs(os.path.join(task_context.path, 'metadata/earkweb'))
        if not os.path.exists(os.path.join(task_context.path, 'metadata/earkweb/migrations')):
            os.makedirs(os.path.join(task_context.path, 'metadata/earkweb/migrations'))

        # create xml file for migration logging
        migration_root = objectify.Element('migrations', attrib={'source': 'source representation',
                                                                 'target': 'target representation',
                                                                 'total': ''})

        # migration policy
        pdf = ['fmt/14', 'fmt/15', 'fmt/16', 'fmt/17', 'fmt/18', 'fmt/19', 'fmt/20', 'fmt/276']
	pdf = []
        pdf_software = subprocess32.check_output(['convert', '-version']).replace('\n', '')     # ImageMagick version
        gif = ['fmt/3', 'fmt/4']
	gif = []
        image_software = subprocess32.check_output(['ghostscript', '-version']).replace('\n', '')   # Ghostscript version

        tl = task_context.task_logger

        # list of all representations in submission folder
        rep_path = os.path.join(task_context.path, 'submission/representations/')
        replist = []
        for repdir in os.listdir(rep_path):
            replist.append(repdir)

        # begin migrations
        total = 0

        # start migrations from every representation
        for rep in replist:
            source_rep_data = '%s/data' % rep
            migration_source = os.path.join(rep_path, source_rep_data)
            migration_target = ''
            target_rep = ''
            outputfile = ''

            # Unix-style pattern matching: if representation directory is in format of <name>_mig-<number>,
            # the new representation will be <number> + 1. Else, it is just <name>_mig-1.
            if fnmatch.fnmatch(rep, '*_mig-*'):
                rep, iteration = rep.rsplit('_mig-', 1)
                target_rep = '%s_mig-%s' % (rep, (int(iteration)+1).__str__())
                target_rep_data = 'representations/%s/data' % target_rep
                migration_target = os.path.join(task_context.path, target_rep_data)
            else:
                target_rep = '%s_mig-%s' % (rep, '1')
                target_rep_data = 'representations/%s/data' % target_rep
                migration_target = os.path.join(task_context.path, target_rep_data)

            # needs to walk from top-level dir of representation data
            for directory, subdirectories, filenames in os.walk(migration_source):
                for filename in filenames:
                    # fido, file format identification
                    identification = FormatIdentification()
                    fido_result = identification.identify_file(os.path.join(directory, filename))
                    self.args = ''
                    if fido_result in pdf:
                        software = pdf_software
                        tl.addinfo('File %s is queued for migration to PDF/A.' % filename)
                        outputfile = filename.rsplit('.', 1)[0] + '.pdf'
                        cliparams = {'output_file': '-sOutputFile=' + os.path.join(migration_target, filename),
                                     'input_file': os.path.join(directory, filename)}
                        self.args = CliCommand.get('pdftopdfa', cliparams)
                    elif fido_result in gif:
                        software = image_software
                        tl.addinfo('File %s is queued for migration to TIFF.' % filename)
                        outputfile = filename.rsplit('.', 1)[0] + '.tiff'
                        cliparams = {'input_file': os.path.join(directory, filename),
                                     'output_file': os.path.join(migration_target, outputfile)}
                        self.args = CliCommand.get('totiff', cliparams)
                    else:
                        tl.addinfo('Unclassified file %s, fido result: %s. This file will NOT be migrated.' % (filename, fido_result))

                    if self.args != '':
                        id = uuid.uuid4().__str__()

                        # additional_data = dict(task_context.additional_data.items() + input.items())
                        context = DefaultTaskContext(task_context.uuid, task_context.path, 'workers.tasks.MigrationProcess', None, task_context.additional_data, None)

                        # create folder for new representation (if it doesnt exist already)
                        if not os.path.exists(migration_target):
                            os.makedirs(migration_target)

                        # create folder for migration process task "feedback" (if it doesnt exist)
                        if not os.path.exists(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s') % target_rep):
                            os.makedirs(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s') % target_rep)

                        # queue the MigrationProcess task
                        try:
                            migrationtask = MigrationProcess()
                            details = {'filename': filename,
                                       'source': migration_source,
                                       'target': migration_target,
                                       'targetrep': target_rep,
                                       'taskid': id.decode('utf-8'),
                                       'commandline': self.args}

                            # use kwargs, those can be seen in Celery Flower
                            migrationtask.apply_async((context,), kwargs=details, queue='default', task_id=id)

                            tl.addinfo('Migration queued for %s.' % filename, display=False)
                        except Exception, e:
                            tl.adderr('Migration task %s for file %s could not be queued: %s' % (id, filename, e))

                        # migration.xml entry - need this for Premis creation. Can put additional stuff here if desired.
                        objectify.SubElement(migration_root, 'migration', attrib={'file': filename,
                                                                                  'output': outputfile,
                                                                                  'sourcedir': migration_source,
                                                                                  'targetdir': migration_target,
                                                                                  'targetrep': target_rep,
                                                                                  'taskid': id,
                                                                                  'status': 'queued',
                                                                                  'starttime': current_timestamp(),
                                                                                  'agent': software})
                        total += 1
                    else:
                        pass

        migration_root.set('total', total.__str__())

        str = etree.tostring(migration_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

        xml_path = os.path.join(task_context.path,'metadata/earkweb/migrations.xml')
        with open(xml_path, 'w') as output_file:
            output_file.write(str)

        tl.addinfo('%d migrations have been queued, please check the progress with the task AIPCheckMigrationProgress.' % total)

        task_context.task_status = 0
        return task_context.additional_data


class MigrationProcess(ConcurrentTask):

    accept_input_from = [AIPMigrations.__name__, SIPValidation.__name__, 'MigrationProcess', 'AIPCheckMigrationProgress']

    def custom_logging(self, filename, events):
        with open(filename, 'a') as logfile:
            for event in events:
                logfile.write(event + '\n')

    def run_task(self, task_context, *args, **kwargs):
        """
        File Migration

        To prevent concurrency problems, this task does not use the default logging to earkweb.log. Instead one log file
         for every migration process is created. They can be found in metadata/earkweb/migrations/. The files follow the
         template of <taskid>.<task_status>, where 1 equals to .fail and 0 to .success.

        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:9,type:0,stage:0
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'MigrationProcess'

        # custom logging
        customlog = []

        customlog.append('%s\tMigration task started for file: %s' % (ts_date(), kwargs['filename']))
        taskid = ''

        try:
            # TODO: additional sub-structure of rep-id/data/... when creating target path
            filename = kwargs['filename']
            taskid = kwargs['taskid']
            self.targetrep = kwargs['targetrep']
            logpath = os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.' % (self.targetrep, taskid))
            self.args = kwargs['commandline']

            # TODO: error handling (OSException)
            if self.args != '':
                # tl.addinfo("subprocess32.Popen args: %s" % self.args)
                self.migrate = subprocess32.Popen(self.args)
                # note: the following line has to be there, even if nothing is done with out/err messages,
                # as the process will otherwise deadlock!
                out, err = self.migrate.communicate()
                if err == None:
                    print 'Successfully migrated file %s.' % filename
                else:
                    print 'Migration for file %s caused errors: %s' % (filename, err)
                    customlog.append('%s\tMigration caused errors: %s' % (ts_date(), err))
                    self.custom_logging(logpath + 'fail', customlog)
                    return task_context.additional_data
            else:
                task_context.task_status = 1
                customlog.append('%s\tMigration for file %s could not be executed due to missing command line parameters.' % (ts_date(), filename))
                self.custom_logging(logpath + 'fail', customlog)
                return task_context.additional_data

            task_context.task_status = 0
            customlog.append('%s\tMigration successful.' % ts_date())
            self.custom_logging(logpath + 'success', customlog)
            return task_context.additional_data
        except SoftTimeLimitExceeded:
            # exceeded time limit for this task, terminate the subprocess, set task status to 1, return False
            self.migrate.terminate()
            task_context.task_status = 1
            customlog.append('%s\tTime limit exceeded, stopping migration.' % ts_date())
            self.custom_logging(logpath + 'fail', customlog)
        except Exception:
            e = sys.exc_info()[0]
            task_context.task_status = 1
            customlog.append('%s\tException in MigrationProcess(): %s' % (ts_date(), e))
            self.custom_logging(logpath + 'fail', customlog)
        return task_context.additional_data


class AIPCheckMigrationProgress(DefaultTask):

    accept_input_from = [AIPMigrations.__name__, MigrationProcess.__name__, 'AIPCheckMigrationProgress']

    def run_task(self, task_context):
        """
        AIP Check Migration Progess

        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:10,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'N/A'

        tl = task_context.task_logger

        total = 0
        successful = 0
        failed = 0

        try:
            xml = os.path.join(task_context.path, 'metadata/earkweb/migrations.xml')
            migrations =  etree.iterparse(open(xml), events=('start',))
            migration_root = ''
            for event, element in migrations:
                if element.tag == 'migrations':
                    total = element.attrib['total']
                    migration_root = element
                elif element.tag == 'migration':
                    if element.attrib['status'] == 'queued':
                        taskid = element.attrib['taskid']
                        target_rep = element.attrib['targetrep']
                        target_file = os.path.join(element.attrib['targetdir'], element.attrib['output'])
                        if os.path.isfile(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.success' % (target_rep, taskid))):
                            # TODO: check if there is actually a file at migration target location - problem: different file extensions (at least)
                            if os.path.isfile(target_file) and os.path.getsize(target_file) > 0:
                                element.set('status', 'successful')
                                # TODO:
                                # element.set('endtime', '')
                                successful += 1
                                # remove the file, to avoid storing huge numbers of useless files
                                # os.remove(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.success' % (target_rep, taskid)))
                            else:
                                tl.adderr('The file %s does not exist, although the migration process reported success!' % target_file)
                        elif os.path.isfile(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.fail' % (target_rep, taskid))):
                            element.set('status', 'failed')
                            failed += 1
                        else:
                            pass
                    elif element.attrib['status'] == 'successful':
                        successful += 1
                    elif element.attrib['status'] == 'failed':
                        failed += 1
                    else:
                        tl.addinfo('Custom status detected, can\'t handle it.')
                else:
                    pass

            missing = int(total) - successful - failed
            tl.addinfo('From a total of %s migrations, %d have been successful and %d failed. Not yet completed: %d migrations.' % (total, successful, failed, missing))

            # write updated file
            str = etree.tostring(migration_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
            xml_path = os.path.join(task_context.path,'metadata/earkweb/migrations.xml')
            with open(xml_path, 'w') as output_file:
                output_file.write(str)
                output_file.close()

            # check if migrations are all completed
            if int(total) == successful:
                tl.addinfo('Migrations completed successfully.')
                task_context.additional_data['migration_complete']=True
                task_context.task_status = 0
                # pack all migration log files into a tar container
                path = os.path.join(task_context.path, 'metadata/earkweb/migrations')
                logfiles = os.listdir(path)
                with tarfile.open(os.path.join(path, 'migrations.tar'), 'w') as tar:
                    os.chdir(path)
                    for logdir in logfiles:
                        tar.add(logdir)  # add to .tar
                        shutil.rmtree(logdir)   # remove
            elif failed > 0 and missing == 0:
                tl.addinfo('Migrations are complete, but a number of them failed.')
                task_context.additional_data['migration_complete']=False
                task_context.task_status = 1
            else:
                tl.addinfo('Migrations are still running, please check back later.')
                task_context.additional_data['migration_complete']=False
                task_context.task_status = 0

        except:
            tl.addinfo('Something went wrong when checking task status.')
            print 'Something went wrong when checking task status.'
            task_context.additional_data['migration_complete']=False
            task_context.task_status = 1

        return task_context.additional_data

class CreatePremisAfterMigration(DefaultTask):

    accept_input_from = [AIPCheckMigrationProgress.__name__, 'CreatePremisAfterMigration']

    def run_task(self, task_context):
        """
        Create Premis After Migration

        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:11,type:2,stage:2
        """

        tl = task_context.task_logger
        if not os.path.exists(os.path.join(task_context.path, 'representations')):
            task_context.task_status = 0
            return task_context.additional_data

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Migration PREMIS Creation'

        for repdir in os.listdir(os.path.join(task_context.path, 'representations')):
            try:
                rep_path = os.path.join(task_context.path, 'representations/%s' % repdir)
                premis_info = {'info': os.path.join(task_context.path, 'metadata/earkweb/migrations.xml')}
                premisgen = PremisGenerator(rep_path)
                premisgen.createMigrationPremis(premis_info)
                tl.addinfo('Generated a Premis file for the representation %s.' % repdir)
                task_context.task_status = 0
            except Exception:
                tl.adderr('Premis generation for representation %s failed.' % repdir)
                task_context.task_status = 1
        return task_context.additional_data


class AIPRepresentationMetsCreation(DefaultTask):

    accept_input_from = [CreatePremisAfterMigration.__name__, 'AIPRepresentationMetsCreation']

    def run_task(self, task_context):
        """
        AIP Representation Mets Creation

        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:12,type:2,stage:2
        """

        if not os.path.exists(os.path.join(task_context.path, 'representations')):
            task_context.task_status = 0
            return task_context.additional_data

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Representation METS Creation'

        tl = task_context.task_logger

        try:
            # copy schema files
            schemalist = os.listdir(os.path.join(root_dir, 'earkresources/schemas'))
            if not os.path.exists(os.path.join(task_context.path, 'schemas')): os.mkdir(os.path.join(task_context.path, 'schemas'))
            for schemafile in schemalist:
                if os.path.isfile(os.path.join(root_dir, 'earkresources/schemas/%s' % schemafile)):
                    shutil.copy2(os.path.join(root_dir, 'earkresources/schemas/%s' % schemafile), os.path.join(task_context.path, 'schemas'))
        except Exception:
            tl.adderr('Error when copying schema files.')

        # schema file location for Mets generation
        schemas = os.path.join(task_context.path, 'schemas')

        # for every REPRESENTATION without METS file:
        for repdir in os.listdir(os.path.join(task_context.path, 'representations')):
            try:
                rep_path = os.path.join(task_context.path, 'representations/%s' % repdir)
                # TODO: packageid?
                # parent = task_context.additional_data['parent_id']
                mets_data = {'packageid': repdir,
                             'type': 'AIP',
                             'schemas': schemas,
                             'parent': ''}
                metsgen = MetsGenerator(rep_path)
                metsgen.createMets(mets_data)

                tl.addinfo('Generated a Mets file for representation %s.' % repdir)
                task_context.task_status = 0
            except Exception:
                tl.adderr('Mets generation for representation %s failed.' % repdir)
                task_context.task_status = 1
        return task_context.additional_data


class AIPPackageMetsCreation(DefaultTask):

    accept_input_from = [AIPRepresentationMetsCreation.__name__, CreatePremisAfterMigration.__name__, "AIPPackageMetsCreation"]

    def run_task(self, task_context):
        """
        AIP Package Mets Creation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:13,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Package Mets Creation'

        tl = task_context.task_logger

        try:
            # copy schema files
            schemalist = os.listdir(os.path.join(root_dir, 'earkresources/schemas'))
            if not os.path.exists(os.path.join(task_context.path, 'schemas')): os.mkdir(os.path.join(task_context.path, 'schemas'))
            for schemafile in schemalist:
                if os.path.isfile(os.path.join(root_dir, 'earkresources/schemas/%s' % schemafile)):
                    shutil.copy2(os.path.join(root_dir, 'earkresources/schemas/%s' % schemafile), os.path.join(task_context.path, 'schemas'))
        except Exception:
            tl.adderr('Error when copying schema files.')

        try:
            # schema file location for Mets generation
            schemas = os.path.join(task_context.path, 'schemas')

            if not 'identifier' in task_context.additional_data:
                tl.adderr('Missing identifier property in task_context.additional_data.')
            identifier = task_context.additional_data['identifier']

            if not 'parent_id' in task_context.additional_data:
                tl.adderr('Missing parent_id property in task_context.additional_data.')
            parent = task_context.additional_data['parent_id']

            mets_data = {'packageid': identifier,
                         'type': 'AIP',
                         'schemas': schemas,
                         'parent': parent}

            metsgen = MetsGenerator(task_context.path)
            metsgen.createMets(mets_data)

            #TODO: get structMap from submission root METS, translate SIP packagename to
            #AIP UUID and add it to the AIP root METS

            # get identifier_map from task_context
            identifier_map = getIdentifierMapFromContext(task_context)
            if identifier_map:
                # check if packagename is in the identifier map
                packagename = task_context.additional_data['packagename']
                if packagename in identifier_map:
                    identifier = identifier_map[packagename]
                    tl.addinfo("Provided identifier assigned: %s" % identifier)
                else:
                    tl.adderr("Cannot find uuid for package name %s in provided identifier_map" % packagename)
                    task_context.task_status = 1
                    return task_context.additional_data

                METS_NS = 'http://www.loc.gov/METS/'
                XLINK_NS = "http://www.w3.org/1999/xlink"

                # parse submission SIP mets
                parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
                sip_mets_path = os.path.join(task_context.path, 'submission', 'METS.xml')
                #print sip_mets_path
                sip_parse = etree.parse(sip_mets_path, parser)
                sip_root = sip_parse.getroot()

                # parse package AIP METS and append children and parent structMaps
                aip_mets_path = os.path.join(task_context.path, 'METS.xml')
                aip_parse = etree.parse(aip_mets_path, parser)
                aip_root = aip_parse.getroot()

                # get children structMap and replace the urn:uuid:packagename with corresponding urn:uuid:uuid
                children_map = sip_root.find("%s[@LABEL='child %s']" % (q(METS_NS, 'structMap'), 'SIP'))
                if children_map is not None:
                    children_map.set('LABEL', 'child AIP')
                    children_div = children_map.find("%s[@LABEL='child %s identifiers']" % (q(METS_NS, 'div'), 'SIP'))
                    children_div.set('LABEL', 'child AIP identifiers')
                    children = children_div.findall("%s[@LABEL='child %s']" % (q(METS_NS, 'div'), 'SIP'))
                    for child in children:
                        child.set('LABEL', 'child AIP')
                        mptr = child.find("%s" % q(METS_NS, 'mptr'))
                        urn = mptr.get(q(XLINK_NS, 'href'))
                        urn = urn.split('urn:uuid:',1)[1]
                        uuid = identifier_map[urn]
                        mptr.set(q(XLINK_NS,'href'), 'urn:uuid:'+uuid)
                        mptr.set(q(XLINK_NS,'title'), 'Referencing a child AIP.')
                    aip_root.append(children_map)
                # get parents structMap and replace the urn:uuid:packagename with corresponding urn:uuid:uuid
                parents_map = sip_root.find("%s[@LABEL='parent %s']" % (q(METS_NS, 'structMap'), 'SIP'))
                if parents_map is not None:
                    parents_map.set('LABEL', 'parent AIP')
                    parents_div = parents_map.find("%s[@LABEL='parent %s identifiers']" % (q(METS_NS, 'div'), 'SIP'))
                    parents_div.set('LABEL', 'parent AIP identifiers')
                    parents = parents_div.findall("%s[@LABEL='parent %s']" % (q(METS_NS, 'div'), 'SIP'))
                    for parent in parents:
                        parent.set('LABEL', 'parent AIP')
                        mptr = parent.find("%s" % q(METS_NS, 'mptr'))
                        urn = mptr.get(q(XLINK_NS,'href'))
                        urn = urn.split('urn:uuid:',1)[1]
                        uuid = identifier_map[urn]
                        mptr.set(q(XLINK_NS,'href'), 'urn:uuid:'+uuid)
                        mptr.set(q(XLINK_NS,'title'), 'Referencing a parent AIP.')
                    aip_root.append(parents_map)

                str = etree.tostring(aip_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
                with open(aip_mets_path, 'w') as output_file:
                    output_file.write(str)

            task_context.task_status = 0
            tl.addinfo('METS updated with AIP content.')

        except Exception, err:
            logger.debug("AN ERROR OCCURRED when processing package %s" % task_context.additional_data['packagename'])
            logger.debug(err)
            tb = traceback.format_exc()
            logger.debug(tb)
            task_context.task_status = 1

        return task_context.additional_data


class AIPValidation(DefaultTask):

    accept_input_from = [AIPPackageMetsCreation.__name__, 'AIPValidation']

    def run_task(self, task_context):
        """
        AIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:14,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIP Validation'

        tl = task_context.task_logger

        try:
            valid = True

            # TODO: return errors and logs?
            mets_validator = MetsValidation(task_context.path)
            result = mets_validator.validate_mets(os.path.join(task_context.path, 'METS.xml'))
            valid = True if result == True else False
            tl.addinfo('Validation result for METS.xml is %s.' % (result))
            for rep, metspath in mets_validator.subsequent_mets:
                print 'METS file for representation: %s at path: %s' % (rep, metspath)
                subsequent_mets_validator = MetsValidation(task_context.path)
                sub_result = subsequent_mets_validator.validate_mets(metspath)
                if valid == True and sub_result == False:
                    valid = False
                tl.addinfo('Validation for the %s Mets file is %s.' % (rep, sub_result))

            # force true validation for showcase
            # valid = True

            task_context.task_status = 0 if valid else 1
        except Exception, err:
            task_context.status = 1
        return task_context.additional_data


class AIPPackaging(DefaultTask):

    accept_input_from = [AIPValidation.__name__, "AIPPackaging"]

    def run_task(self, task_context):
        """
        AIP Packaging
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:15,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'N/A'

        tl = task_context.task_logger

        try:
            # identifier (not uuid of the working directory) is used as first part of the tar file
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            tl.addinfo("Packaging working directory: %s" % task_context.path)
            # append generation number to tar file; if tar file exists, the generation number is incremented
            new_id = task_context.additional_data["identifier"]
            #storage_path = task_context.additional_data["storage_path"]
            storage_file = os.path.join(task_context.path, "%s.tar" % new_id)
            tar = tarfile.open(storage_file, "w:")
            tl.addinfo("Creating archive: %s" % storage_file)

            total = sum([len(files) for (root, dirs, files) in walk(task_context.path)])
            tl.addinfo("Total number of files in working directory %d" % total)
            # log file is closed at this point because it will be included in the package,
            # subsequent log messages can only be shown in the gui

            #file_elements, delivery_xml = getDeliveryFiles(task_context.path)
            # continue normally we have only one tar
            #file_reference = ParsedMets.get_file_element_reference(file_elements[0])

            #tl.addinfo("Extracted file reference: %s" % file_reference)
            #delivery_file = os.path.join(task_context.path, os.path.basename(remove_protocol(file_reference)))

            package_name = task_context.additional_data['packagename']
            delivery_xml = os.path.join(task_context.path, "%s.xml" % package_name)
            delivery_file_tar = os.path.join(task_context.path, "%s.tar" % package_name)
            delivery_file_zip = os.path.join(task_context.path, "%s.zip" % package_name)

            status_xml = os.path.join(task_context.path, "state.xml")
            submission_status_xml = os.path.join(task_context.path, "submission/state.xml")
            tl.addinfo("Ignoring package file (tar): %s" % delivery_file_tar)
            tl.addinfo("Ignoring package file (zip): %s" % delivery_file_zip)
            tl.addinfo("Ignoring delivery XML file: %s" % delivery_xml)
            tl.addinfo("Ignoring status XML file: %s" % status_xml)
            tl.addinfo("Ignoring submission status XML file: %s" % submission_status_xml)

            # ignore files that were only needed to check on migration status
            # ignore_dir = os.path.join(task_context.path, 'metadata/earkweb')

            ignore_list = [delivery_file_tar, delivery_file_zip, delivery_xml, status_xml, submission_status_xml]
            i = 0
            for subdir, dirs, files in os.walk(task_context.path):
                # if subdir == ignore_dir:
                #     # remove files and subfolders from loop, so they are not packaged
                #     del dirs[:]
                #     del files[:]
                for file in files:
                    if os.path.join(subdir, file) not in ignore_list:
                        entry = os.path.join(subdir, file)
                        arcname = new_id + "/" + os.path.relpath(entry, task_context.path)
                        tar.add(entry, arcname = arcname)
                        if i % 10 == 0:
                            perc = (i * 100) / total
                            self.update_state(state='PROGRESS', meta={'process_percent': perc})
                    i += 1
            tar.close()
            tl.log.append("Package created: %s" % storage_file)

            #ip.statusprocess = tc.success_status if result.success else tc.error_status
            #ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            task_context.task_status = 0
        except Exception, err:
            task_context.task_status = 0
        return task_context.additional_data


class AIPStore(DefaultTask):

    accept_input_from = [AIPPackaging.__name__, "AIPStore", "AIPIndexing"]

    def run_task(self, task_context):
        """
        Store AIP
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:16,type:2,stage:2
        """

        # no premis event
        #task_context.event_type = 'AIPStore'

        tl = task_context.task_logger

        parent_path = task_context.additional_data['parent_path'].__str__()

        if len(parent_path) > 0:
            if os.path.isfile(os.path.join(parent_path, 'METS.xml')):
                metsgen = MetsGenerator(parent_path)
                metsgen.addChildRelation(task_context.additional_data['identifier'])
            else:
                tl.adderr('No Mets file found in the parent AIP, you must create one.')
                task_context.task_status = 1
                return task_context.additional_data
        else:
            tl.addinfo('There is no parent AIP for this AIP.')

        try:
            package_id = task_context.additional_data["identifier"]
            storePath = task_context.additional_data["storage_dest"]
            if not task_context.additional_data['storage_dest']:
                tl.adderr("Storage root must be defined to execute this task.")
            else:
                # copy the package
                tarfile_path = "%s/%s.tar" % (task_context.path, package_id)
                if not os.path.exists(tarfile_path):
                    tl.adderr("Unable to store package. The package container file does not exist: %s." % tarfile_path)
                else:
                    # abspath_basename = "%s/%s" % (storePath, package_id)
                    # tarfile_dest = increment_file_name_suffix(abspath_basename, "tar")
                    # shutil.copy2(tarfile_path, tarfile_dest)
                    pts = PairtreeStorage(storePath)
                    pts.store(package_id, tarfile_path)
                    package_object_path = pts.get_object_path(package_id)
                    if os.path.exists(package_object_path):
                        tl.addinfo('Storage path: %s' % (package_object_path))
                        if ChecksumFile(tarfile_path).get(ChecksumAlgorithm.SHA256) == ChecksumFile(package_object_path).get(ChecksumAlgorithm.SHA256):
                            tl.addinfo("Checksum verification completed, the package was transmitted successfully.")
                            task_context.additional_data["storage_loc"] = package_object_path
                        else:
                            tl.adderr("Checksum verification failed, an error occurred while trying to transmit the package.")
                    else:
                        tl.adderr("Error storing package")
            task_context.task_status = 1 if (len(tl.err) > 0) else 0
        except Exception as e:
            tl.adderr("Task failed: %s" % e.message)
            tl.adderr(traceback.format_exc())
            task_context.task_status = 1
        return task_context.additional_data

class AIPIndexing(DefaultTask):

    accept_input_from = [AIPStore.__name__, 'SolrUpdateCurrentMetadata', "AIPIndexing"]

    def run_task(self, task_context):
        """
        AIP Index
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:17,type:2,stage:2
        """

        # no premis event
        task_context.event_type = None

        # task logger
        tl = task_context.task_logger

        # check required parameters in task context
        parameters = ["storage_dest", "identifier"]
        if not task_context.has_required_parameters(parameters):
            task_context.task_status = 0
            return task_context.report_parameter_errors(parameters)

        # check solr server availability
        from config.configuration import local_solr_server_ip
        from config.configuration import local_solr_port
        solr_server = SolrServer(local_solr_server_ip, local_solr_port)
        tl.addinfo("Solr server base url: %s" % solr_server.get_base_url())
        sq = SolrQuery(solr_server)
        r = requests.get(sq.get_base_url())
        if not r.status_code == 200:
            tl.adderr("Solr server is not available at: %s" % sq.get_base_url())
            task_context.task_status = 2
            return task_context.additional_data

        storage_dest = task_context.additional_data["storage_dest"]
        tl.addinfo("Storage path: %s" % storage_dest)
        identifier = task_context.additional_data["identifier"]
        pts = PairtreeStorage(storage_dest)

        # check if the repository container is available for the given identifier
        if not pts.identifier_object_exists(identifier):
            tl.adderr("Object for identifier does not exist in repository.")
            task_context.task_status = 0
            return task_context.additional_data

        try:
            # initialize solr client
            solr_client = SolrClient(solr_server, "earkstorage")
            # post documents of repository container to solr server
            partial_custom_progress_reporter = partial(custom_progress_reporter, self)
            tl.addinfo("Object path: %s" % pts.get_object_path(identifier))
            results = solr_client.post_tar_file(pts.get_object_path(identifier), identifier, partial_custom_progress_reporter)
            tl.addinfo("Total number of files posted: %d" % len(results))
            num_ok = sum(1 for result in results if result['status'] == 200)
            tl.addinfo("Number of files posted successfully: %d" % num_ok)
            num_failed = sum(1 for result in results if result['status'] != 200)
            tl.addinfo("Number of plain documents: %d" % num_failed)
            task_context.task_status = 1 if (len(tl.err) > 0) else 0
        except Exception as e:
            tl.adderr("AIP indexing task failed: %s" % e.message)
            tl.adderr(traceback.format_exc())
            task_context.task_status = 2
        return task_context.additional_data


def update_solr_doc(task_context, element, solr_field_name):
    tl = task_context.task_logger
    # instantiate Solr communication class
    solr = SolrUtility()
    index_path = element['path']
    index_md_value = element['mdvalue']
    # need a solr query to retrieve identifier: solr.solr_unique_key
    identifier_query_param = (task_context.additional_data['identifier']).replace(":", "\\:")
    query_result = solr.send_query('path:%s%s' % (identifier_query_param, index_path.replace(task_context.path, '')))
    if query_result is not False:
        try:
            identifier = None
            if "lily.key" in query_result[0]:
                identifier = query_result[0]['lily.key']
            else:
                identifier = query_result[0]['id']
        except Exception, e:
            tl.adderr('Retrieving unique identifier failed: %s' % e.message)

        tl.addinfo("Updating field '%s' of solr record '%s' with value '%s'" %(solr_field_name, identifier, index_md_value))

        if solr_field_name.endswith("_dt"):
            lbdf = LengthBasedDateFormat(index_md_value)
            index_md_value = lbdf.reformat()

        # update 'eadtitle' field afterwards; '_t' marks it as text_general
        update = solr.set_field(record_identifier=identifier,
                                field=solr_field_name,
                                content=index_md_value)

        if update == 200:
            tl.addinfo('%s updated with status code 200.' % index_path)
            task_context.task_status = 0
        else:
            tl.adderr('%s failed with status code %d.' % (index_path, update))
            task_context.task_status = 1
    else:
        tl.adderr('Query status code: %s' % query_result)


class SolrUpdateCurrentMetadata(DefaultTask):

    accept_input_from = [AIPStore.__name__, AIPIndexing.__name__, "SolrUpdateCurrentMetadata"]

    def run_task(self, task_context):
        """
        AIP Index
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:18,type:2,stage:2
        """

        # no premis event
        task_context.event_type = None

        tl = task_context.task_logger
        tl.addinfo("Updating SolR records with metadata.")

        submiss_dir = 'submission'
        md_dir = 'metadata'
        md_subdir_descr = 'descriptive'

        descriptive_md_dir = os.path.join(md_dir, md_subdir_descr)
        submiss_descr_md_dir = os.path.join(task_context.path, submiss_dir, descriptive_md_dir)
        overruling_metadata_dir = os.path.join(task_context.path, md_dir, submiss_dir, descriptive_md_dir)

        tl.addinfo("Looking for EAD metadata files in metadata directory: %s" % strip_prefixes(submiss_descr_md_dir, task_context.path))

        # "warning" state for validation errors
        try:
            md_files_valid = []
            from earkcore.utils.fileutils import find_files
            for filename in find_files(submiss_descr_md_dir, metadata_file_pattern_ead):
                md_path, md_file = os.path.split(filename)
                tl.addinfo("Found descriptive metadata file in submission folder: '%s'" % md_file)
                tl.addinfo("Looking for overruling version in AIP metadata folder: '%s'" % strip_prefixes(overruling_metadata_dir, task_context.path))
                overruling_md_file = os.path.join(overruling_metadata_dir, md_file)
                validation_md_path = md_path
                if os.path.exists(overruling_md_file):
                    tl.addinfo("Overruling version of descriptive metadata file found: %s" % strip_prefixes(overruling_md_file, task_context.path))
                    validation_md_path = overruling_metadata_dir
                else:
                    tl.addinfo("No overruling version of descriptive metadata file in AIP metadata folder found.")
                tl.addinfo("Using EAD metadata file: %s" % filename)

                extract_defs = [
                    {'ead_element': 'unittitle', 'solr_field': 'eadtitle_s'},
                    {'ead_element': 'unitdate', 'solr_field': 'eaddate_s'},
                    {'ead_element': 'unitid', 'solr_field': 'eadid_s'},
                    {'ead_element': 'unitdatestructured', 'solr_field': 'eaddatestructuredfrom_dt', 'text_access_path': 'ead:datesingle'},
                    {'ead_element': 'unitdatestructured', 'solr_field': 'eaddatestructuredto_dt', 'text_access_path': 'ead:datesingle'},
                    {'ead_element': 'origination', 'solr_field': 'eadorigination_s', 'text_access_path': 'ead:corpname/ead:part'},
                    {'ead_element': 'abstract', 'solr_field': 'eadabstract_t', 'text_access_path': None},
                    {'ead_element': 'accessrestrict', 'solr_field': 'eadaccessrestrict_s', 'text_access_path': 'ead:head'},
                    {'ead_element': '[Cc][0,1][0-9]', 'solr_field': 'eadclevel_s', 'text_access_path': 'level', 'is_attribute': True},
                ]
                result = field_namevalue_pairs_per_file(extract_defs, validation_md_path, filename)
                solr = SolrUtility()
                for k in result.keys():
                    safe_urn_identifier = (task_context.additional_data['identifier']).replace(":", "\\:")
                    entry_path = k.replace(task_context.path, '')
                    identifier = solr.get_doc_id_from_path(safe_urn_identifier, entry_path)
                    status_code = solr.update_document(identifier, result[k])
                    tl.addinfo("Solr document %s updated for file item: %s (return code: %s)" % (identifier, entry_path, status_code))
                md_files_valid.append(validate_ead_metadata(validation_md_path, md_file, None, tl))
            if len(md_files_valid) == 0:
                tl.addinfo("No descriptive metadata files found.")
            valid = False not in md_files_valid
            if valid:
                tl.addinfo("Descriptive metadata validation completed successfully.")
            task_context.task_status = 0 if valid else 2
        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2


class LilyHDFSUpload(DefaultTask):

    accept_input_from = [AIPStore.__name__, AIPIndexing.__name__, "LilyHDFSUpload"]

    def run_task(self, task_context):
        """
        AIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:19,type:2,stage:2
        """
        # no premis event
        #task_context.event_type = 'LilyHDFSUpload'

        tl = task_context.task_logger
        try:
            aip_path = task_context.additional_data["storage_loc"]
            if not aip_path:
                tl.adderr("Required context parameter \"storage location\" (storage_loc) is missing")
            if not (aip_path and os.path.exists(aip_path)):
                tl.adderr("Unable to access container package at the given storage location: %s" % aip_path)
            if len(tl.err) == 0:
                tl.addinfo("Start uploading AIP %s from local path: %s" % (task_context.uuid, aip_path))
                # Reporter function which will be passed via the HDFSRestClient to the FileBinaryDataChunks.chunks()
                # method where the actual reporting about the upload progress occurs.
                rest_endpoint = RestEndpoint("http://%s:%s" % (hdfs_upload_service_ip, hdfs_upload_service_port), hdfs_upload_service_endpoint_path)
                tl.addinfo("Using REST endpoint: %s" % (rest_endpoint.to_string()))
                # Partial application of the custom_progress_reporter function so that the task object
                # is known to the FileBinaryDataChunks.chunks() method.
                partial_custom_progress_reporter = partial(custom_progress_reporter, self)
                hdfs_rest_client = HDFSRestClient(rest_endpoint, partial_custom_progress_reporter)
                rest_resource_path_pattern = "%s{0}" % hdfs_upload_service_resource_path
                upload_result = hdfs_rest_client.upload_to_hdfs(aip_path, rest_resource_path_pattern)
                tl.addinfo("Upload finished in %d seconds with status code %d: %s" % (time.time() - task_context.start_time, upload_result.status_code, upload_result.hdfs_path_id))
                checksum_resource_uri = "%s%s/digest/sha-256" % (hdfs_upload_service_resource_path, upload_result.hdfs_path_id)
                tl.addinfo("Verifying checksum at %s" % (checksum_resource_uri))
                hdfs_sha256_checksum = hdfs_rest_client.get_string(checksum_resource_uri)
                if ChecksumFile(aip_path).get(ChecksumAlgorithm.SHA256) == hdfs_sha256_checksum:
                    tl.addinfo("Checksum verification completed, the package was transmitted successfully.")
                else:
                    tl.adderr("Checksum verification failed, an error occurred while trying to transmit the package.")
        except Exception, err:
            tl.adderr("An error occurred: %s" % err)
        task_context.task_status = 2 if (len(tl.err) > 0) else 0
        return task_context.additional_data


class AIPtoDIPReset(DefaultTask):

    accept_input_from = ['All']

    def run_task(self, task_context):
        """
        SIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1000,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIPtoDIPReset'

        # create working directory if it does not exist
        if not os.path.exists(task_context.path):
            fileutils.mkdir_p(task_context.path)

        representations_path = os.path.join(task_context.path, "representations")
        if os.path.exists(representations_path):
            shutil.rmtree(representations_path)

        #remove and recreate empty directories
        # data_path = os.path.join(task_context.path, "data")
        # if os.path.exists(data_path):
        #     shutil.rmtree(data_path)
        # mkdir_p(data_path)
        # task_context.task_logger.addinfo("New empty 'data' directory created")

        metadata_path = os.path.join(task_context.path, "metadata")
        if os.path.exists(metadata_path):
            shutil.rmtree(metadata_path)
        mkdir_p(metadata_path)
        task_context.task_logger.addinfo("New empty 'metadata' directory created")

        # remove extracted sips
        tar_files = glob.glob("%s/*.tar" % task_context.path)
        for tar_file in tar_files:
            tar_base_name, _ = os.path.splitext(tar_file)
            if os.path.exists(tar_base_name):
                shutil.rmtree(tar_base_name)
            task_context.task_logger.addinfo("Extracted AIP folder '%s' removed" % tar_base_name)

        # remove representations folder if existing
        rep_folder = os.path.join(task_context.path, "representations")
        if os.path.exists(rep_folder):
            shutil.rmtree(rep_folder)
            task_context.task_logger.addinfo("Generated DIP representations folder '%s' removed" % rep_folder)

        # remove schemas folder from root if existing
        schemas_folder = os.path.join(task_context.path, "schemas")
        if os.path.exists(schemas_folder):
            shutil.rmtree(schemas_folder)
            task_context.task_logger.addinfo("Generated DIP schemas folder '%s' removed" % schemas_folder)

        mets_file = os.path.join(task_context.path, "METS.xml")
        if os.path.exists(mets_file):
            os.remove(mets_file)
            task_context.task_logger.addinfo("Generated root METS.xml removed")

        # reset identifier
        task_context.additional_data['identifier'] = ''
        task_context.task_logger.addinfo("Identifier removed.")

        # success status
        task_context.task_status = 0
        return task_context.additional_data


class DIPAcquireAIPs(DefaultTask):

    accept_input_from = ['DIPAcquireAIPs', AIPtoDIPReset.__name__]

    def run_task(self, task_context):
        """
        SIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1010,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPAcquireAIPs'

        tl = task_context.task_logger
        try:
            # create dip working directory
            if not os.path.exists(task_context.path):
                os.mkdir(task_context.path)
            # packagename is identifier of the DIP creation process
            #dip = DIP.objects.get(name=task_context.task_name)

            total_bytes_read = 0
            aip_total_size = 0

            selected_aips = task_context.additional_data["selected_aips"]
            print "selected AIPs: %s" % selected_aips
            for aip_source in selected_aips.values():
                if not os.path.exists(aip_source):
                    tl.adderr("Missing AIP source %s" % aip_source)
                    tl.adderr("Task failed %s" % task_context.uuid)
                    task_context.task_status = 1
                    return task_context.additional_data
                else:
                    aip_total_size+=fsize(aip_source)

            task_context.additional_data["selected_aips"] = selected_aips.keys()

            tl.addinfo("DIP: %s, total size: %d" % (task_context.task_name, aip_total_size))
            #for aip in dip.aips.all():
            for aip_identifier, aip_source in selected_aips.iteritems():
                aip_source_size = fsize(aip_source)
                partial_custom_progress_reporter = partial(custom_progress_reporter, self)
                package_extension = aip_source.rpartition('.')[2]
                aip_in_dip_work_dir = os.path.join(task_context.path, ("%s.%s" % (aip_identifier, package_extension)))
                tl.addinfo("Source: %s (%d)" % (aip_source, aip_source_size))
                tl.addinfo("Target: %s" % (aip_in_dip_work_dir))
                with open(aip_in_dip_work_dir, 'wb') as target_file:
                    for chunk in FileBinaryDataChunks(aip_source, 65536, partial_custom_progress_reporter).chunks(total_bytes_read, aip_total_size):
                        target_file.write(chunk)
                    total_bytes_read += aip_source_size
                    target_file.close()
                check_transfer(aip_source, aip_in_dip_work_dir, tl)
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            task_context.task_status = 0
        except Exception as e:
            tl.adderr("Task failed %s" % task_context.uuid)
            tb = traceback.format_exc()
            tl.adderr(str(tb))
            task_context.task_status = 2

        return task_context.additional_data


def get_aip_parent(task_context_path, aip_identifier, package_extension):
    aip_in_dip_work_dir = os.path.join(task_context_path, ("%s.%s" % (aip_identifier, package_extension)))

    # get parent and children from existing AIP tar (aip_in_dip_work_dir)
    METS_NS = 'http://www.loc.gov/METS/'
    XLINK_NS = "http://www.w3.org/1999/xlink"
    print "reading METS of selected aip %s" % aip_in_dip_work_dir
    with tarfile.open(aip_in_dip_work_dir) as tar:
        mets_file = aip_identifier+'/METS.xml'
        member = tar.getmember(mets_file)
        fp = tar.extractfile(member)
        mets_content = fp.read()

        # parse AIP mets
        parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
        aip_parse = etree.parse(StringIO(mets_content), parser)
        aip_root = aip_parse.getroot()

        # find AIP structmap and parent identifiers
        parents_map = aip_root.find("%s[@LABEL='parent %s']" % (q(METS_NS, 'structMap'), 'AIP'))
        if parents_map is not None:
            parents_div = parents_map.find("%s[@LABEL='parent %s identifiers']" % (q(METS_NS, 'div'), 'AIP'))
            if parents_div is not None:
                parents = parents_div.findall("%s[@LABEL='parent %s']" % (q(METS_NS, 'div'), 'AIP'))
                for parent in parents:
                    mptr = parent.find("%s" % q(METS_NS, 'mptr'))
                    urn = mptr.get(q(XLINK_NS,'href'))
                    uuid = urn.split('urn:uuid:',1)[1]
                    print "found parent uuid %s" % uuid
                    return uuid

    return None

def get_aip_children(task_context_path, aip_identifier, package_extension):
    aip_in_dip_work_dir = os.path.join(task_context_path, ("%s.%s" % (aip_identifier, package_extension)))

    children_uuids = []
    # get parent and children from existing AIP tar (aip_in_dip_work_dir)
    METS_NS = 'http://www.loc.gov/METS/'
    XLINK_NS = "http://www.w3.org/1999/xlink"
    print "reading METS of selected aip %s" % aip_in_dip_work_dir
    with tarfile.open(aip_in_dip_work_dir) as tar:
        mets_file = aip_identifier+'/METS.xml'
        member = tar.getmember(mets_file)
        fp = tar.extractfile(member)
        mets_content = fp.read()

        # parse AIP mets
        parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
        aip_parse = etree.parse(StringIO(mets_content), parser)
        aip_root = aip_parse.getroot()

        # find AIP structmap and child identifiers
        children_map = aip_root.find("%s[@LABEL='child %s']" % (q(METS_NS, 'structMap'), 'AIP'))
        if children_map is not None:
            children_div = children_map.find("%s[@LABEL='child %s identifiers']" % (q(METS_NS, 'div'), 'AIP'))
            if children_div is not None:
                children = children_div.findall("%s[@LABEL='child %s']" % (q(METS_NS, 'div'), 'AIP'))
                for child in children:
                    mptr = child.find("%s" % q(METS_NS, 'mptr'))
                    urn = mptr.get(q(XLINK_NS, 'href'))
                    print "found child urn %s" % urn
                    uuid = urn.split('urn:uuid:',1)[1]
                    print "found child uuid %s" % uuid
                    children_uuids.append(uuid)
    return children_uuids

def get_package_from_storage(task_context_path, package_uuid, package_extension, tl):
    from config.configuration import config_path_storage
    pts = PairtreeStorage(config_path_storage)
    parent_object_path = pts.get_object_path(package_uuid)

    package_in_dip_work_dir = os.path.join(task_context_path, ("%s.%s" % (package_uuid, package_extension)))
    package_source_size = fsize(parent_object_path)
    tl.addinfo("Source: %s (%d)" % (parent_object_path, package_source_size))
    tl.addinfo("Target: %s" % package_in_dip_work_dir)
    total_bytes_read = 0
    with open(package_in_dip_work_dir, 'wb') as target_file:
         for chunk in FileBinaryDataChunks(parent_object_path, 65536).chunks(total_bytes_read):
             target_file.write(chunk)
         total_bytes_read += package_source_size
         target_file.close()
    check_transfer(parent_object_path, package_in_dip_work_dir, tl)

def get_children_from_storage(task_context_path, package_uuid, package_extension, tl):
    get_package_from_storage(task_context_path, package_uuid, package_extension, tl)
    child_uuids = get_aip_children(task_context_path, package_uuid, package_extension)
    for child_uuid in child_uuids:
        get_children_from_storage(task_context_path, child_uuid, package_extension, tl)


class DIPAcquireDependentAIPs(DefaultTask):

    accept_input_from = ['All', DIPAcquireAIPs.__name__]

    def run_task(self, task_context):
        """
        DIPAcquireDependentAIPs
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1020,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPAcquireDependentAIPs'

        tl = task_context.task_logger
        try:
            # create dip working directory
            if not os.path.exists(task_context.path):
                os.mkdir(task_context.path)

            storePath = task_context.additional_data["storage_dest"]
            if not task_context.additional_data['storage_dest']:
                tl.adderr("Storage root must be defined to execute this task.")
                task_context.task_status = 1
                return task_context.additional_data

            # packagename is identifier of the DIP creation process
            #dip = DIP.objects.get(name=task_context.task_name)

            selected_aips = task_context.additional_data["selected_aips"]
            tl.addinfo("selected AIPs: %s" % selected_aips)

            aip_parents = []
            for aip_identifier, aip_source in selected_aips.iteritems():
                #TODO: get package_extension from METS as is not necessarily the same
                package_extension = aip_source.rpartition('.')[2]
                head_parent = None
                while True:
                    parent_uuid = get_aip_parent(task_context.path, aip_identifier, package_extension)
                    if parent_uuid:
                        #get the parent from storage
                        get_package_from_storage(task_context.path, parent_uuid, package_extension, tl)
                        aip_identifier = parent_uuid
                        head_parent = parent_uuid
                    else:
                        print "Head Parent UUID %s" % head_parent
                        aip_parents.append(head_parent)
                        break

            for aip_parent in aip_parents:
                get_children_from_storage(task_context.path, aip_parent, package_extension, tl)

            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            task_context.task_status = 0
        except Exception as e:
            tl.adderr("Task failed: %s" % e.message)
            tl.adderr(traceback.format_exc())
            task_context.task_status = 1
        return task_context.additional_data


class DIPExtractAIPs(DefaultTask):

    accept_input_from = ['All', DIPAcquireAIPs.__name__, DIPAcquireDependentAIPs.__name__, "DIPExtractAIPs"]

    def run_task(self, task_context):
        """
        DIP Extract AIPs
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1030,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPExtractAIPs'

        tl = task_context.task_logger

        selected_aips = task_context.additional_data["selected_aips"]
        for selected_aip in selected_aips:
            tl.addinfo(str(selected_aip))

        try:
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            # create dip working directory
            if not os.path.exists(task_context.path):
                os.mkdir(task_context.path)

            # packagename is identifier of the DIP creation process
            selected_aips = task_context.additional_data["selected_aips"]

            total_members = 0
            for aip_identifier, aip_source in selected_aips.iteritems():
                if not os.path.exists(aip_source):
                    tl.adderr("Missing AIP source %s" % aip_source)
                    tl.adderr("Task failed %s" % task_context.uuid)
                    task_context.task_status = 1
                    return task_context.additional_data
                else:
                    package_extension = aip_source.rpartition('.')[2]
                    aip_in_dip_work_dir = os.path.join(task_context.path, ("%s.%s" % (aip_identifier, package_extension)))
                    tar_obj = tarfile.open(name=aip_in_dip_work_dir, mode='r', encoding='utf-8')
                    members = tar_obj.getmembers()
                    total_members += len(members)
                    tar_obj.close()

            tl.addinfo("Total number of entries: %d" % total_members)
            total_processed_members = 0
            perc = 0
            for aip_identifier, aip_source in selected_aips.iteritems():
                package_extension = aip_source.rpartition('.')[2]
                aip_in_dip_work_dir = os.path.join(task_context.path, ("%s.%s" % (aip_identifier, package_extension)))
                tl.addinfo("Extracting: %s" % aip_in_dip_work_dir)
                tar_obj = tarfile.open(name=aip_in_dip_work_dir, mode='r', encoding='utf-8')
                members = tar_obj.getmembers()
                current_package_total_members = 0
                for member in members:
                    if total_processed_members % 10 == 0:
                        perc = (total_processed_members * 100) / total_members
                        self.update_state(state='PROGRESS', meta={'process_percent': perc})
                    tar_obj.extract(member, task_context.path)
                    tl.addinfo(("File extracted: %s" % member.name), display=False)
                    total_processed_members += 1
                    current_package_total_members += 1

                tl.addinfo("Untar of %d items from package %s finished" % (current_package_total_members, aip_identifier))
            tl.addinfo(("Untar of %d items in total finished" % total_processed_members))
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            task_context.task_status = 0

            # Add related AIPs to PREMIS based on the extracted AIP directories available in the working directory
            premis_path = os.path.join(task_context.path, 'metadata/preservation/premis.xml')
            from earkcore.metadata.mets.metsutil import get_mets_objids_from_basedir
            extracted_aips = get_mets_objids_from_basedir(task_context.path)
            from earkcore.metadata.premis.dippremis import DIPPremis
            if os.path.isfile(premis_path):
                dip_premis = DIPPremis(premis_path)
                dip_premis.add_related_aips(extracted_aips, 'DIPAcquireAIPs')
                with open(premis_path, 'w') as output_file:
                    output_file.write(str(dip_premis))
            tl.addinfo("Related AIPs added to PREMIS: %s" % ", ".join(extracted_aips))
        except Exception as e:
            tl.adderr("Task failed %s" % task_context.uuid)
            tl.adderr("Task failed %s" % e.message)
            task_context.task_status = 1

        return task_context.additional_data

from subprocess import Popen, PIPE
def runCommand(args, stdin=PIPE, stdout=PIPE, stderr=PIPE):
        result, res_stdout, res_stderr = None, None, None
        try:
            # quote the executable otherwise we run into troubles
            # when the path contains spaces and additional arguments
            # are presented as well.
            # special: invoking bash as login shell here with
            # an unquoted command does not execute /etc/profile

            print 'Launching: %s' % args
            process = Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=False)

            res_stdout, res_stderr = process.communicate()
            result = process.returncode
            print 'Finished: %s' % args

        except Exception as ex:
            res_stderr = ''.join(str(ex.args))
            result = 1

        if result != 0:
            print 'Command failed:' + ''.join(res_stderr)
            raise Exception('Command failed:' + ''.join(res_stderr))

        return result, res_stdout, res_stderr


class DIPImportSIARD(DefaultTask):

    accept_input_from = ['All', DIPExtractAIPs.__name__, "DIPImportSIARD"]

    def run_task(self, task_context):
        """
        DIP Extract AIPs
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1040,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPImportSIARD'
        tl = task_context.task_logger
        siard_dbs = []

        try:
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            # find SIARD2 file in working dir
            for root, dirs, files in os.walk(task_context.path):
                for file in files:
                    if file.endswith(".siard2"):
                        siard_path = os.path.join(root, file)
                        tl.addinfo(("SIARD file found at: %s" % siard_path))
                        siard_db_name = os.path.splitext(file)[0]

                        tl.addinfo("Creating new database: %s" % siard_db_name)
                        # drop database if existing
                        command = [
                            'mysql',
                            'mysql',
                            '-u', siard_db_user,
                            '-p%s' % siard_db_passwd,
                            '-e', 'DROP DATABASE IF EXISTS %s;' % siard_db_name,
                            ]
                        runCommand(command)
                        # create database
                        command = [
                            'mysql',
                            'mysql',
                            '-u', siard_db_user,
                            '-p%s' % siard_db_passwd,
                            '-e', 'CREATE DATABASE IF NOT EXISTS %s;' % siard_db_name,
                            ]
                        runCommand(command)
                        # import file to database
                        command = [
                            'java', '-jar', siard_dbptk,
                            '-i', 'siard-2',
                            '-if', siard_path,
                            '-e', siard_db_type,
                            '-eh', siard_db_host,
                            '-edb', siard_db_name,
                            '-eu', siard_db_user,
                            '-ep', siard_db_passwd,
                        ]
                        tl.addinfo("Importing SIARD file '%s' to database '%s'." % (siard_path, siard_db_name))
                        runCommand(command)
                        #java -jar $DBPTK -i siard-2 --import-file=world.siard2 -e mysql --export-hostname=localhost --export-database=world --export-user=$USER --export-password=$PASSWORD
                        siard_dbs.append(siard_db_name)

            task_context.additional_data['siard_dbs'] = siard_dbs
            task_context.task_status = 0

        except Exception as e:
            tl.adderr("Task failed %s" % task_context.uuid)
            tl.adderr("Task failed %s" % e.message)
            task_context.task_status = 1

        print "additional_data %s" % task_context.additional_data
        return task_context.additional_data


class DIPExportSIARD(DefaultTask):

    accept_input_from = ['All', DIPImportSIARD.__name__, "DIPExportSIARD"]

    def run_task(self, task_context):
        """
        DIP Extract AIPs
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1050,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPExportSIARD'
        tl = task_context.task_logger

        print "additional_data %s" % task_context.additional_data

        if not "siard_dbs" in task_context.additional_data:
            print "Task parameter \"siard_dbs\" missing"
            tl.adderr("Task parameter \"siard_dbs\" missing")
            task_context.task_status = 1
            return task_context.additional_data

        siard_dbs = task_context.additional_data["siard_dbs"]

        #create representations/siard_rep/data folder
        siard_data_path = os.path.join(task_context.path, 'representations', 'siard_rep', 'data')
        if not os.path.exists(siard_data_path):
            os.makedirs(siard_data_path)

        #create metadata folder
        siard_metadata_path = os.path.join(task_context.path, 'representations', 'siard_rep', 'metadata', 'preservation')
        if not os.path.exists(siard_metadata_path):
            os.makedirs(siard_metadata_path)

        try:
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            for siard_db_name in siard_dbs:
                # create representations directory (aka path to dump siard)
                tl.addinfo("Dumping Database %s to %s" % (siard_db_name, siard_data_path))
                siard_path = os.path.join(siard_data_path, siard_db_name+'.siard2')
                # export database to file
                command = [
                    'java', '-jar', siard_dbptk,
                    '-i', siard_db_type,
                    '--import-hostname', siard_db_host,
                    '-idb', siard_db_name,
                    '-iu', siard_db_user,
                    '-ip', siard_db_passwd,
                    '-e', 'siard-2',
                    '-ef', siard_path,
                ]
                runCommand(command)
                #java -jar $DBPTK -i mysql -ih=localhost -idb world -iu $USER -ip $PASSWORD -e siard-2 -ef world.siard2
            task_context.task_status = 0

        except Exception as e:
            tl.adderr("Task failed %s" % task_context.uuid)
            tl.adderr("Task failed %s" % e.message)
            task_context.task_status = 1

        return task_context.additional_data


class DIPGMLDataValidation(DefaultTask):

    accept_input_from = [DIPImportSIARD.__name__, DIPExportSIARD.__name__, DIPExtractAIPs.__name__, 'DIPGMLDataValidation']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1060,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'GML Data Validation'

        tl = task_context.task_logger
        tl.addinfo("Looking for GML data files in the package: %s" % task_context.path)

        # "warning" state for validation errors
        try:
            gml_files_valid = []
            from earkcore.utils.fileutils import find_files
            for filename in find_files(task_context.path, "*.gml"):
                path, md_file = os.path.split(filename)
                tl.addinfo("Found GML file '%s'" % md_file)
                gml_proc = PeripleoGmlProcessing(filename)
                gml_files_valid.append(gml_proc.conversion_conditions_fulfilled())
                if gml_proc.err and len(gml_proc.err) > 0:
                    tl.adderr("Error in GML file '%s'" % md_file)
                    for error in gml_proc.err:
                        tl.adderr("- %s" % error)
                if gml_proc.log and len(gml_proc.log) > 0:
                    for info_item in gml_proc.log:
                        tl.addinfo("- %s" % info_item.encode('utf-8').strip())
                if not gml_proc.err or (gml_proc.err and len(gml_proc.err) == 0):
                    tl.addinfo("- Peripleo conversion conditions fulfilled")
            if len(gml_files_valid) == 0:
                tl.addinfo("No GML data files found.")
            valid = False not in gml_files_valid
            if valid:
                tl.addinfo("GML data file validation completed successfully.")
            task_context.task_status = 0 if valid else 2

        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2
        return task_context.additional_data


class DIPGMLDataConversion(DefaultTask):

    accept_input_from = [DIPExtractAIPs.__name__, DIPImportSIARD.__name__, DIPGMLDataValidation.__name__, 'DIPGMLDataConversion']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1070,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'GML Data Conversion'
        self.update_state(state='PROGRESS', meta={'process_percent': 0})

        tl = task_context.task_logger
        package_root_dir = os.path.join(task_context.path)
        tl.addinfo("Looking for GML data files in package root: %s" % package_root_dir)

        from config.configuration import django_service_ip, django_service_port
        # "warning" state for validation errors
        uri_part = "http://%s:%s/earkweb/sip2aip/working_area/aip2dip/%s/" % (django_service_ip, django_service_port, task_context.uuid)
        try:
            from earkcore.utils.fileutils import find_files
            num_gml_files = sum([1 for f in find_files(package_root_dir, "*.gml")])
            tl.addinfo("Found %d GML files in working directory" % num_gml_files)
            if num_gml_files > 0:
                ttl_rep_data_dir = 'representations/peripleottl/data'
                peripleottl_data_dir = os.path.join(task_context.path, ttl_rep_data_dir)
                if not os.path.exists(peripleottl_data_dir):
                    mkdir_p(peripleottl_data_dir)
                i = 0
                for gml_file_path in find_files(package_root_dir, "*.gml"):
                    path, gml_file = os.path.split(gml_file_path)
                    file_name, ext = os.path.splitext(gml_file)
                    ttl_file_path = os.path.join(peripleottl_data_dir, "%s.ttl" % file_name)
                    file_name_parts = file_name.split("_")
                    specific_part = randomword(5) if len(file_name_parts) != 2 else file_name_parts[1]
                    gml_proc = PeripleoGmlProcessing(gml_file_path)
                    gml_proc.convert_gml(ttl_file_path, uri_part, specific_part)
                    perc = (i * 100) / num_gml_files
                    self.update_state(state='PROGRESS', meta={'process_percent': perc})
                    tl.addinfo("GML file '%s' converted to TTL file '%s" % (gml_file_path, ttl_file_path))
                    i += 1
            else:
                tl.addinfo("No GML files in working directory")
            task_context.task_status = 0
        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2
        return task_context.additional_data


class DIPPeripleoDeployment(DefaultTask):

    accept_input_from = [DIPGMLDataConversion.__name__, 'DIPPeripleoDeployment']

    def run_task(self, task_context):
        """
        DIP Peripleo Deployment run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1080,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIP Peripleo Deployment'
        self.update_state(state='PROGRESS', meta={'process_percent': 0})

        tl = task_context.task_logger
        gazetteers_json = None
        try:
            from config.configuration import peripleo_server_ip, peripleo_port, peripleo_path
            rest_endpoint = RestEndpoint("http://%s:%s" % (peripleo_server_ip, peripleo_port), peripleo_path)
            urllib2.urlopen(rest_endpoint.get_endpoint_uri())
            tl.addinfo("Peripleo server available at %s" % rest_endpoint.get_endpoint_uri())
            gazetteers_response = urllib2.urlopen(rest_endpoint.get_resource_uri("gazetteers"))
            if gazetteers_response.getcode() == 200:
                gazetteers_json = json.loads(gazetteers_response.read())
            else:
                tl.adderr("Error: Unable to retrieve gazetteers list from Peripleo.")
                task_context.task_status = 2
                return task_context.additional_data
        except urllib2.URLError, err:
            tl.adderr("Peripleo server unavailable: %s" % err.reason)
            tl.adderr("According to the configuration the Peripleo endpoint must be available at: %s" % rest_endpoint.get_endpoint_uri())
            task_context.task_status = 2
            return task_context.additional_data

        representations_dir = os.path.join(task_context.path, 'representations/peripleottl')
        tl.addinfo("Looking for TTL data files in peripleo representation directory: %s" % representations_dir)
        # "warning" state when errors occur
        try:
            from earkcore.utils.fileutils import find_files
            num_ttl_files = sum([1 for f in find_files(representations_dir, "*.ttl")])
            tl.addinfo("Found %d TTL files in working directory" % num_ttl_files)
            if num_ttl_files > 0:
                i = 0
                for ttl_file_path in find_files(representations_dir, "*.ttl"):
                    _, ttl_file_name = os.path.split(ttl_file_path)
                    peripleo_client = RestClient(rest_endpoint)
                    ttl_file_path_without_ext, _ = os.path.splitext(ttl_file_path)
                    logger.info("Deployment of file: '%s'" % ttl_file_name)
                    if not any(gazetteer['name'] == ttl_file_path_without_ext for gazetteer in gazetteers_json):
                        if peripleo_client.post_file("admin/gazetteers", "rdf", ttl_file_path):
                            logger.info("Peripleo deployment request sent successfully")
                        else:
                            logger.error("Error sending Peripleo deployment request")
                        # one request per second
                        time.sleep(1)
                    else:
                        tl.addinfo("TTL file deployed already: %s" % ttl_file_path)
                        tl.addinfo("Remove gazetteer '%s' from Peripleo to redeploy" % ttl_file_path_without_ext)
                    perc = (i * 100) / num_ttl_files
                    self.update_state(state='PROGRESS', meta={'process_percent': perc})
                    i += 1
            else:
                tl.addinfo("No GML files in working directory")
            task_context.task_status = 0
        except Exception, err:
            tb = traceback.format_exc()
            tl.adderr("An error occurred: %s" % err)
            tl.adderr(str(tb))
            task_context.task_status = 2
        return task_context.additional_data


class DIPMetadataCreation(DefaultTask):

    # Descriptive metadata check can be skipped
    accept_input_from = [SIPReset.__name__, DIPExtractAIPs.__name__, DIPExportSIARD.__name__, 'DIPMetadataCreation']

    def run_task(self, task_context):
        """
        SIP Package metadata creation run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1090,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPMetadataCreation'

        reps_path = os.path.join(task_context.path, 'representations')
        if os.path.isdir(reps_path):
            for name in os.listdir(reps_path):
                rep_path = os.path.join(reps_path, name)
                if os.path.isdir(rep_path):
                    # Premis
                    premisgen = PremisGenerator(rep_path)
                    premisgen.createPremis()
                    # Mets
                    mets_data = {'packageid': task_context.uuid,
                                 'type': 'DIP',
                                 'schemas': os.path.join(task_context.path, 'schemas'),
                                 'parent': ''}
                    metsgen = MetsGenerator(rep_path)
                    metsgen.createMets(mets_data)
        else:
            task_context.task_logger.addinfo("No DIP representations found.")

        # Premis not needed as already existing
        #premisgen = PremisGenerator(task_context.path)
        #premisgen.createPremis()

        # create DIP parent Mets
        mets_data = {'packageid': task_context.uuid,
                     'type': 'DIP',
                     'schemas': os.path.join(task_context.path, 'schemas'),
                     'parent': ''}
        metsgen = MetsGenerator(task_context.path)
        metsgen.createMets(mets_data)

        # copy schemas folder from extracted tar to root
        selected_aips = task_context.additional_data["selected_aips"]
        src_schemas_folder = os.path.join(task_context.path, selected_aips.keys()[0], 'schemas')
        dst_schemas_folder = os.path.join(task_context.path, 'schemas')
        shutil.copytree(src_schemas_folder, dst_schemas_folder)

        task_context.task_status = 0
        return task_context.additional_data


class DIPIdentifierAssignment(DefaultTask):

    accept_input_from = [DIPMetadataCreation.__name__, "DIPIdentifierAssignment"]

    def run_task(self, task_context):
        """
        Identifier Assignment run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1100,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIP Identifier Assignment'

        tl = task_context.task_logger

        # Get new identifier
        identifier = randomutils.getUniqueID() # "urn:uuid:%s" %
        task_context.additional_data['identifier'] = identifier

        # Set identifier in METS
        try:
            mets_path = os.path.join(task_context.path, 'METS.xml')
            if os.path.isfile(mets_path):
                # If the Premis file exists, replace every events <linkingObjectIdentifierValue> with the new
                # identifier, as well as the <objectIdentifierValue> for the object resembling the package.
                parsed_mets = etree.parse(mets_path)
                root = parsed_mets.getroot()
                root.set('OBJID', 'urn:uuid:%s' % identifier)

                # write changed METS file
                mets_content = etree.tostring(parsed_mets, encoding='UTF-8', pretty_print=True, xml_declaration=True)
                with open(mets_path, 'w') as output_file:
                    output_file.write(mets_content)
                tl.addinfo("DIP identifier set in METS file.")
                task_context.task_status = 0
            else:
                tl.adderr('Can\'t find a METS file to update it with new identifier!')
                task_context.task_status = 1
        except Exception, e:
            tl.adderr('An error ocurred when trying to update the METS file with the new identifier: %s' % str(e))
            tl.adderr(traceback.format_exc())
            task_context.task_status = 1
            return task_context.additional_data

        # Set identifier in PREMIS
        try:
            if os.path.isfile(os.path.join(task_context.path, 'metadata/preservation/premis.xml')):
                # If the Premis file exists, replace every events <linkingObjectIdentifierValue> with the new
                # identifier, as well as the <objectIdentifierValue> for the object resembling the package.
                premis_path = os.path.join(task_context.path, 'metadata/preservation/premis.xml')
                PREMIS_NS = 'info:lc/xmlns/premis-v2'
                parsed_premis = etree.parse(premis_path)

                object = parsed_premis.find(q(PREMIS_NS, 'object'))
                object_id_value = object.find('.//%s' % q(PREMIS_NS, 'objectIdentifierValue'))
                object_id_value.text = identifier

                events = parsed_premis.findall(q(PREMIS_NS, 'event'))
                for event in events:
                    event_rel_obj = event.find('.//%s' % q(PREMIS_NS, 'linkingObjectIdentifierValue'))
                    event_rel_obj.text = identifier

                # write the changed Premis file
                str = etree.tostring(parsed_premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
                with open(premis_path, 'w') as output_file:
                    output_file.write(str)
                tl.addinfo("DIP identifier set in PREMIS file.")
                task_context.task_status = 0
            else:
                tl.adderr('Can\'t find a Premis file to update it with new identifier!')
                task_context.task_status = 1
        except Exception, e:
            tl.adderr('An error ocurred when trying to update the Premis file with the new identifier: %s' % e)
            task_context.task_status = 1
            return task_context.additional_data

        task_context.additional_data['identifier'] = identifier

        tl.addinfo("New identifier assigned: %s" % identifier)
        return task_context.additional_data


class DIPPackaging(DefaultTask):

    accept_input_from = [DIPIdentifierAssignment.__name__, "DIPPackaging"]

    def run_task(self, task_context):
        """
        AIP Packaging
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1110,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'N/A'

        tl = task_context.task_logger

        dip_identifier = task_context.additional_data['identifier']

        try:
            # identifier (not uuid of the working directory) is used as first part of the tar file
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            tl.addinfo("Packaging working directory: %s" % task_context.path)

            storage_file = os.path.join(task_context.path, "%s.tar" % dip_identifier)
            tar = tarfile.open(storage_file, "w:")
            tl.addinfo("Creating archive: %s" % storage_file)

            item_list = ['metadata', 'representations', 'schemas', 'METS.xml']
            total = 0
            for item in item_list:
                pack_item = os.path.join(task_context.path, item)
                if os.path.isdir(pack_item):
                    total += sum([len(files) for (root, dirs, files) in walk(pack_item)])
                else:
                    total += 1
            tl.addinfo("Total number of files in working directory %d" % total)
            # log file is closed at this point because it will be included in the package,
            # subsequent log messages can only be shown in the gui

            i = 0
            for item in item_list:
                pack_item = os.path.join(task_context.path, item)
                if os.path.isdir(pack_item):
                    for subdir, dirs, files in os.walk(pack_item):
                        for file in files:
                            if os.path.join(subdir, file):
                                entry = os.path.join(subdir, file)
                                arcname = dip_identifier + "/" + os.path.relpath(entry, task_context.path)
                                tar.add(entry, arcname = arcname)
                                if i % 10 == 0:
                                    perc = (i * 100) / total
                                    self.update_state(state='PROGRESS', meta={'process_percent': perc})
                            i += 1
                else:
                    arcname = dip_identifier + "/" + os.path.relpath(pack_item, task_context.path)
                    tar.add(pack_item, arcname = arcname)
                    if i % 10 == 0:
                            perc = (i * 100) / total
                            self.update_state(state='PROGRESS', meta={'process_percent': perc})
                    i += 1
            tar.close()
            tl.log.append("Package created: %s" % storage_file)

            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            task_context.task_status = 0
        except Exception, err:
            task_context.task_status = 0
        return task_context.additional_data


class DIPStore(DefaultTask):

    accept_input_from = [DIPPackaging.__name__, "DIPStore"]

    def run_task(self, task_context):
        """
        Store DIP
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1120,type:4,stage:4
        """

        # no premis event
        #task_context.event_type = 'N/A'

        tl = task_context.task_logger

        from config.configuration import config_path_storage
        if not os.path.exists(os.path.join(config_path_storage, "pairtree_version0_1")):
            tl.adderr("Storage path is not a pairtree storage directory.")
            task_context.task_status = 2
            return task_context.additional_data
        if not ("identifier" in task_context.additional_data.keys() and task_context.additional_data["identifier"] != ""):
            tl.adderr("DIP identifier is not defined.")
            task_context.task_status = 2
            return task_context.additional_data
        package_identifier = task_context.additional_data["identifier"]
        package_file_name = "%s.tar" % task_context.additional_data["identifier"]
        package_file_path = os.path.join(task_context.path, package_file_name)
        if not os.path.exists(package_file_path):
            tl.adderr("DIP TAR package does not exist: %s" % package_file_path)
            task_context.task_status = 2
            return task_context.additional_data
        try:
            pts = PairtreeStorage(config_path_storage)
            pts.store(package_identifier, package_file_path)

            package_object_path = pts.get_object_path(package_identifier)
            if os.path.exists(package_object_path):
                tl.addinfo('Storage path: %s' % (package_object_path))
                if ChecksumFile(package_file_path).get(ChecksumAlgorithm.SHA256) == ChecksumFile(package_object_path).get(ChecksumAlgorithm.SHA256):
                    tl.addinfo("Checksum verification completed, the package was transmitted successfully.")
                    task_context.additional_data["storage_loc"] = package_object_path
                else:
                    tl.adderr("Checksum verification failed, an error occurred while trying to transmit the package.")
            task_context.task_status = 1 if (len(tl.err) > 0) else 0
        except Exception as e:
            tl.adderr("Task failed: %s" % e.message)
            tl.adderr(traceback.format_exc())
            task_context.task_status = 1
        return task_context.additional_data


class DMMainTask(ConcurrentTask):

    accept_input_from = 'All'

    def run_task(self, task_context, *args, **kwargs):
        """
        DMMMainTask
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:0,type:0,stage:0
        """

        ner_model = kwargs['ner_model']
        # category_model = kwargs['category_model']
        tar_path = '%s.tar' % os.path.join(nlp_storage_path, kwargs['tar_path'])
        logger.debug('Creating/using tar at following path: %s' % tar_path)

        if 'solr_query' in kwargs:
            print kwargs['solr_query']
            query = kwargs['solr_query']

            archive_creator = CreateNLPArchive()
            archive_creator.get_data_from_solr(solr_query=query, archive_name=tar_path)
        else:
            pass

        # initialise NLP tasks
        ner_task = DMNERecogniser()
        # cat_task = DMTextCategoriser()    # TODO

        with tarfile.open(tar_path, 'r') as tar:
            for filename in tar.getmembers():
                content = tar.extractfile(filename).read()
                if ner_model is not 'None':
                    details = {'model': ner_model,
                               'identifier': filename.name}
                    taskid = uuid.uuid4().__str__()
                    t_context = DefaultTaskContext('', '', 'workers.tasks.DMNERecogniser', None, '', None)
                    t_context.file_content = content
                    ner_task.apply_async((t_context,), kwargs=details, queue='default', task_id=taskid)
                # if cat is not 'None':
                #     pass

        return task_context.additional_data


class DMNERecogniser(ConcurrentTask):

    accept_input_from = [DMMainTask.__name__]

    def run_task(self, task_context, *args, **kwargs):
        """
        DMNERecogniser
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:0,type:0,stage:0
        """
        # TODO: add geo-referencing?

        content = task_context.file_content
        identifier = kwargs['identifier']
        model = kwargs['model']

        # initialise tagger
        jar = os.path.join(stanford_jar, 'stanford-ner.jar')
        model = os.path.join(stanford_ner_models, model)
        tagger = StanfordNERTagger(model, jar, encoding='utf-8', java_options='-mx8000m')

        print 'initialised with model: %s' % model
        print 'now tagging: %s' % identifier

        tokenized = []
        content = content.strip().decode('utf-8')
        tokens = word_tokenize(content, language='english')     # TODO: change tokenizer language dynamically
        for token in tokens:
            tokenized.append(token + '\n')

        # position = 0
        # TODO: make dynamic for more categories!
        organisations_list = []
        persons_list = []
        locations_list = []
        for result in tagger.tag(tokenized):
            if result[1] != 'O':
                if 'LOC' in result[1]:
                    organisations_list.append(result[0])
                elif 'PER' in result[1]:
                    persons_list.append(result[0])
                elif 'ORG' in result[1]:
                    locations_list.append(result[0])

        # update Solr with results
        solr = SolrUtility()
        document_id = solr.send_query('path:"%s"' % identifier)[0]['id']
        loc_status = solr.set_field(document_id, 'locations_ss', locations_list)
        time.sleep(1)
        per_status = solr.set_field(document_id, 'persons_ss', persons_list)
        time.sleep(1)
        org_status = solr.set_field(document_id, 'organisations_ss', organisations_list)

        print 'status for %s' % identifier
        print 'solr identifier: %s' % document_id
        print loc_status, per_status, org_status

        return task_context.additional_data


class IPClose(DefaultTask):

    accept_input_from = [AIPStore.__name__, AIPIndexing.__name__, SolrUpdateCurrentMetadata.__name__, LilyHDFSUpload, DIPStore.__name__]

    def run_task(self, task_context, *args, **kwargs):
        """
        IPClose
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:100000,type:6,stage:0
        """
        if os.path.exists(task_context.path) and task_context.path == os.path.join(config_path_work, task_context.uuid):
            shutil.rmtree(task_context.path)
            task_context.task_logger.addinfo("Working directory deleted: %s" % task_context.path)
        task_context.task_status = 0
        return task_context.additional_data


class IPDelete(DefaultTask):

    accept_input_from = ['All']

    def run_task(self, task_context, *args, **kwargs):
        """
        IPClose
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:100100,type:6,stage:0
        """
        if os.path.exists(task_context.path) and task_context.path == os.path.join(config_path_work, task_context.uuid):
            shutil.rmtree(task_context.path)
            task_context.task_logger.addinfo("Working directory deleted: %s" % task_context.path)
        task_context.task_status = 0
        return task_context.additional_data
