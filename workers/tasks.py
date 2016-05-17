import os
import shutil
import sys
import tarfile
import time
from functools import partial
from os import walk
import traceback
from celery import current_task

import logging
logger = logging.getLogger(__name__)

from config.configuration import mets_schema_file
from config.configuration import root_dir
from config.configuration import config_path_work
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
from earkcore.utils.fileutils import mkdir_p, increment_file_name_suffix
from earkcore.utils.fileutils import remove_fs_item
from earkcore.utils.fileutils import remove_protocol
from earkcore.xml.deliveryvalidation import DeliveryValidation
from earkcore.metadata.task_utils import validate_ead_metadata
from earkweb.celeryapp import app
from sandbox.sipgenerator.sipgenerator import SIPGenerator
from tasklogger import TaskLogger
from workers.default_task import DefaultTask
from earkcore.metadata.XmlHelper import q
import uuid
from earkcore.utils.datetimeutils import current_timestamp
from lxml import etree, objectify
import fnmatch
from workers.default_task_context import DefaultTaskContext
from earkcore.format.formatidentification import FormatIdentification
from earkcore.process.cli.CliCommand import CliCommand
import subprocess32
from earkcore.filesystem.fsinfo import path_to_dict
from celery.exceptions import SoftTimeLimitExceeded
from config.configuration import hdfs_upload_service_ip
import requests
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
def reception_dir_status(self, reception_d):

    reception_dir_status = "%s" % path_to_dict(reception_d)
    reception_dir_status = reception_dir_status.replace("'", "\"")
    return reception_dir_status


@app.task(bind=True)
def run_batch_ingest(self, reception_d):
    print "RUN BATCH INGEST!!!"
    reception_dir_status = "%s" % path_to_dict(reception_d)
    reception_dir_status = reception_dir_status.replace("'", "\"")
    return reception_dir_status


class SIPReset(DefaultTask):

    accept_input_from = ['All']

    def run_task(self, task_context):
        """
        SIP Creation Reset run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'SIPReset'

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
        #task_context.event_type = 'SIPMetadataConsistency'

        tl = task_context.task_logger
        tl.addinfo("EAD metadata file validation.")
        metadata_dir = os.path.join(task_context.path, 'metadata')
        valid = validate_ead_metadata(metadata_dir, 'EAD.xml', None, tl)

        task_context.task_status = 0 if valid else 1
        return task_context.additional_data

class SIPPackageMetadataCreation(DefaultTask):

    # Descriptive metadata check can be skipped
    accept_input_from = [SIPReset.__name__, SIPDescriptiveMetadataValidation.__name__, 'SIPPackageMetadataCreation']

    def run_task(self, task_context):
        """
        SIP Package metadata creation run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:3,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'SIPPackageMetadataCreation'

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
        @param      tc: order:4,type:1,stage:1
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'SIPPackaging'

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



class SIPClose(DefaultTask):

    accept_input_from = [SIPPackaging.__name__, 'SIPClose']

    def run_task(self, task_context):
        """
        SIP Packaging run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:5,type:1,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'SIPClose'

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

    def run_task(self, task_context):
        """
        SIP to AIP Reset run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:1,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = SIPtoAIPReset

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
        #task_context.event_type = 'SIPDeliveryValidation'

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



class IdentifierAssignment(DefaultTask):

    accept_input_from = [SIPDeliveryValidation.__name__, "IdentifierAssignment"]

    def run_task(self, task_context):
        """
        Identifier Assignment run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:3,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'IdentifierAssignment'

        tl = task_context.task_logger

        # TODO: set identifier in METS file
        # TODO: change identifiers used in Premis retroactively
        identifier = randomutils.getUniqueID()
        tl.addinfo("New identifier assigned: %s" % identifier)

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
        #task_context.event_type = 'SIPExtraction'
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
                target_folder = os.path.join(task_context.path, str(delivery))
                package_file_abs_path = os.path.join(task_context.path, package_file)
                tl.addinfo("Extracting package file %s to %s" % (package_file_abs_path,target_folder))
                extr.extract_with_report(package_file_abs_path, target_folder, progress_reporter=custom_reporter)
                #remove packaged state.xml. No need for it anymore
                #state_path = os.path.join(target_folder, "state.xml")
                #if os.path.exists(state_path):
                #    os.remove(state_path)
            tl.log += extr.log
            tl.err += extr.err
            task_context.task_status = 0
        return task_context.additional_data


class SIPRestructuring(DefaultTask):

    accept_input_from = [SIPExtraction.__name__]

    def run_task(self, task_context):
        """
        SIP Restructuring run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:5,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'SIPRestructuring'

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


class SIPValidation(DefaultTask):

    accept_input_from = [SIPRestructuring.__name__,"SIPValidation"]

    def run_task(self, task_context):
        """
        SIP Validation run task
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:6,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'SIPValidation'

        tl = task_context.task_logger
        valid = True

        def check_file(descr, f):
            if os.path.exists(f):
                tl.addinfo("%s found: %s" % (descr, os.path.abspath(f)))
            else:
                tl.adderr(("%s missing: %s" % (descr, os.path.abspath(f))))

        submission_path = os.path.join(task_context.path, "submission")
        check_file("submission METS file", os.path.join(submission_path, "METS.xml"))
        #check_file("Data directory", os.path.join(reps_path, "data"))

        #check_file("Documentation directory", os.path.join(path, "documentation"))
        #check_file("Metadata directory", os.path.join(path, "metadata"))

        # submission is not mandatory in an AIP:
        if os.path.exists(os.path.join(task_context.path, "submission/representations")):
            representations_path = os.path.join(task_context.path, "submission/representations")
            for name in os.listdir(representations_path):
                rep_path = os.path.join(representations_path, name)
                if os.path.isdir(rep_path):
                    mets_validator = MetsValidation(rep_path)
                    valid = mets_validator.validate_mets(os.path.join(rep_path, 'METS.xml'))
                    # TODO: validate possible sub-METS files:
                    # for rep, metspath in mets_validator.subsequent_mets:
                    #     print 'METS file for representation: %s at path: %s' % (rep, metspath)
                    #     subsequent_mets_validator = MetsValidation(task_context.path)
                    #     sub_result = subsequent_mets_validator.validate_mets(metspath)
                    #     if valid == True and sub_result == False:
                    #         valid = False
                    #     tl.addinfo('Validation for the %s Mets file is %s.' % (rep, sub_result))

        # task_context.task_status = 0 if valid else 1
        if valid:
            task_context.task_status = 0
        else:
            task_context.task_status = 1
            for error in mets_validator.validation_errors:
                tl.adderr(error)
        return task_context.additional_data

class AIPMigrations(DefaultTask):

    accept_input_from = [SIPValidation.__name__, 'MigrationProcess', 'AIPMigrations', 'AIPCheckMigrationProgress']

    def run_task(self, task_context):
        """
        AIP File Migration
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:7,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIPMigrations'

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
        gif = ['fmt/3', 'fmt/4']

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
                    self.args= ''
                    if fido_result in pdf:
                        tl.addinfo('File %s is queued for migration to PDF/A.' % filename)
                        outputfile = filename.rsplit('.', 1)[0] + '.pdf'
                        cliparams = {'output_file': '-sOutputFile=' + os.path.join(migration_target, filename),
                                     'input_file': os.path.join(directory, filename)}
                        self.args = CliCommand.get('pdftopdfa', cliparams)
                    elif fido_result in gif:
                        tl.addinfo('File %s is queued for migration to TIFF.' % filename)
                        outputfile = filename.rsplit('.', 1)[0] + '.tiff'
                        cliparams = {'input_file': os.path.join(directory, filename),
                                     'output_file': os.path.join(migration_target, outputfile)}
                        self.args = CliCommand.get('totiff', cliparams)
                    else:
                        tl.addinfo('Unclassified file %s, fido result: %s. This file will NOT be migrated.' % (filename, fido_result))

                    if self.args != '':
                        id = uuid.uuid4().__str__()
                        input = ({'file': filename,
                                  'source': migration_source,
                                  'target': migration_target,
                                  'targetrep': target_rep,
                                  'taskid': id.decode('utf-8'),
                                  'commandline': self.args})

                        additional_data = dict(task_context.additional_data.items() + input.items())
                        context = DefaultTaskContext(task_context.uuid, task_context.path, 'workers.tasks.MigrationProcess', None, additional_data, None)


                        # create folder for new representation (if it doesnt exist already)
                        if not os.path.exists(migration_target):
                            os.makedirs(migration_target)

                        # create folder for migration process task "feedback" (if it doesnt exist)
                        if not os.path.exists(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s') % target_rep):
                            os.makedirs(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s') % target_rep)

                        # queue the MigrationProcess task
                        try:
                            migrationtask = MigrationProcess()
                            migrationtask.apply_async((context,), queue='default', task_id=id)
                            tl.addinfo('Migration queued for %s.' %  filename, display=False)
                        except:
                            tl.adderr('Migration task %s for file %s could not be queued.' % (id, filename))

                        # migration.xml entry - need this for Premis creation. Can put additional stuff here if desired.
                        #TODO: check this out. Not used anywhere Jan??
                        migration = objectify.SubElement(migration_root, 'migration', attrib={'file': filename,
                                                                                              'output': outputfile,
                                                                                              'sourcedir': migration_source,
                                                                                              'targetdir': migration_target,
                                                                                              'targetrep': target_rep,
                                                                                              'taskid': id,
                                                                                              'status': 'queued',
                                                                                              'starttime': current_timestamp(),
                                                                                              'endtime': ''})
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


class MigrationProcess(DefaultTask):
    # TODO: maybe move this class/task to another file? Or call external migration classes for each migration type.

    accept_input_from = [AIPMigrations.__name__, SIPValidation.__name__, 'MigrationProcess', 'AIPCheckMigrationProgress']

    def run_task(self, task_context):
        """
        File Migration
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:8,type:0,stage:0
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'MigrationProcess'

        # print 'current worker:'
        # print multiprocessing.current_process().name

        # TODO: logging does not work perfectly.
        # This is because every subtask of AIPMigrations can only write its changes into the logfile,
        # when the instance of MigrationProcess who opened the log file the first time, closes it (or the AIPMigrations
        # process calls its finalize() method, for that matter).
        # Then the next instance of MigrationProcess can write to the file, and so on. This results in a chaotic
        # earkweb.log file, without chronological order! Look into other solutions, maybe a bytestream?
        tl = task_context.task_logger

        tl.addinfo('Migration task started for file: %s' % task_context.additional_data['file'])

        taskid = ''

        try:
            # TODO: additional sub-structure of rep-id/data/... when creating target path
            file = task_context.additional_data['file']
            taskid = task_context.additional_data['taskid']
            self.targetrep = task_context.additional_data['targetrep']
            self.args = task_context.additional_data['commandline']


            # TODO: error handling (OSException)
            if self.args != '':
                self.migrate = subprocess32.Popen(self.args)
                 # note: the following line has to be there, even if nothing is done with out/err messages,
                 # as the process will otherwise deadlock!
                out, err = self.migrate.communicate()
                if err == None:
                    tl.addinfo('Successfully migrated file %s.' % file)
                    print 'Successfully migrated file %s.' % file
                else:
                    tl.adderr('Migration for file %s caused errors: %s' % (file, err))
                    print 'Migration for file %s caused errors: %s' % (file, err)
                    with open(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.%s'% (self.targetrep, taskid, 'fail')), 'a' ) as status:
                        status.write(err)
                    return task_context.additional_data
            else:
                tl.adderr('Migration for file %s could not be executed due to missing command line parameters.' % file)
                task_context.task_status = 1
                with open(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.%s'% (self.targetrep, taskid, 'fail')), 'a' ) as status:
                    status.write('Migration for file %s could not be executed due to missing command line parameters.' % file)
                return task_context.additional_data

            task_context.task_status = 0
            with open(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.%s'% (self.targetrep, taskid, 'success')), 'a' ) as status:
                pass
            return task_context.additional_data
        except SoftTimeLimitExceeded:
            # exceeded time limit for this task, terminate the subprocess, set task status to 1, return False
            tl.adderr('Time limit exceeded, stopping migration.')
            self.migrate.terminate()
            task_context.task_status = 1
            with open(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.%s'% (self.targetrep, taskid, 'fail')), 'a' ) as status:
                status.write('Time limit exceeded, stopping migration.')
        except Exception:
            e = sys.exc_info()[0]
            tl.adderr('Exception in MigrationProcess(): %s' % e)
            task_context.task_status = 1
            with open(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.%s'% (self.targetrep, taskid, 'fail')), 'a' ) as status:
                status.write('Exception in MigrationProcess(): %s' % e)
        return task_context.additional_data


class AIPCheckMigrationProgress(DefaultTask):

    accept_input_from = [AIPMigrations.__name__, MigrationProcess.__name__, 'AIPCheckMigrationProgress']

    def run_task(self, task_context):
        """
        AIP Check Migration Progess

        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:8,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'AIPCheckMigrationProgress'

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
                                os.remove(os.path.join(task_context.path, 'metadata/earkweb/migrations/%s/%s.success' % (target_rep, taskid)))
                            else:
                                tl.adderr('The file %s does not exists, although the migration process reported success!' % target_file)
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

            # check if migrations are all completed
            if int(total) == successful:
                tl.addinfo('Migrations completed successfully.')
                task_context.additional_data['migration_complete']=True
                task_context.task_status = 0
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
        @param      tc: order:9,type:2,stage:2
        """

        tl = task_context.task_logger
        if not os.path.exists(os.path.join(task_context.path, 'representations')):
            task_context.task_status = 0
            return task_context.additional_data

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'CreatePremisAfterMigration'

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
        @param      tc: order:10,type:2,stage:2
        """

        if not os.path.exists(os.path.join(task_context.path, 'representations')):
            task_context.task_status = 0
            return task_context.additional_data

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIPRepresentationMetsCreation'

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
        @param      tc: order:11,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIPPackageMetsCreation'

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

            task_context.task_status = 0
            tl.addinfo('METS updated with AIP content.')

        except Exception as err:
            tl.addinfo('error: %s' % str(err))
            task_context.task_status = 1

        return task_context.additional_data


class AIPValidation(DefaultTask):

    accept_input_from = [AIPPackageMetsCreation.__name__, 'AIPValidation']

    def run_task(self, task_context):
        """
        AIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:12,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'AIPValidation'

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
        @param      tc: order:13,type:2,stage:2
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'AIPPackaging'

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
            delivery_file = os.path.join(task_context.path, "%s.tar" % package_name)

            status_xml = os.path.join(task_context.path, "state.xml")
            submission_status_xml = os.path.join(task_context.path, "submission/state.xml")
            tl.addinfo("Ignoring package file: %s" % delivery_file)
            tl.addinfo("Ignoring delivery XML file: %s" % delivery_xml)
            tl.addinfo("Ignoring status XML file: %s" % status_xml)
            tl.addinfo("Ignoring submission status XML file: %s" % submission_status_xml)

            # ignore files that were only needed to check on migration status
            ignore_dir = os.path.join(task_context.path, 'metadata/earkweb')

            ignore_list = [delivery_file, delivery_xml, status_xml, submission_status_xml]
            i = 0
            for subdir, dirs, files in os.walk(task_context.path):
                if subdir == ignore_dir:
                    # remove files and subfolders from loop, so they are not packaged
                    del dirs[:]
                    del files[:]
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

    accept_input_from = [AIPPackaging.__name__, "AIPStore"]

    def run_task(self, task_context):
        """
        Store AIP
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:14,type:2,stage:2
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

    accept_input_from = [AIPStore.__name__, "AIPIndexing"]

    def run_task(self, task_context):
        """
        AIP Index
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:15,type:2,stage:2
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
            task_context.task_status = 0
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
            task_context.task_status = 1
        return task_context.additional_data

class LilyHDFSUpload(DefaultTask):

    accept_input_from = [AIPStore.__name__, AIPIndexing.__name__, "LilyHDFSUpload"]

    def run_task(self, task_context):
        """
        AIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:16,type:2,stage:2
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
                rest_endpoint = RestEndpoint("http://%s" % hdfs_upload_service_ip, "dm-hdfs-storage")
                tl.addinfo("Using REST endpoint: %s" % (rest_endpoint.to_string()))
                # Partial application of the custom_progress_reporter function so that the task object
                # is known to the FileBinaryDataChunks.chunks() method.
                partial_custom_progress_reporter = partial(custom_progress_reporter, self)
                hdfs_rest_client = HDFSRestClient(rest_endpoint, partial_custom_progress_reporter)
                rest_resource_path = "hsink/fileresource/files/{0}"
                upload_result = hdfs_rest_client.upload_to_hdfs(aip_path, rest_resource_path)
                tl.addinfo("Upload finished in %d seconds with status code %d: %s" % (time.time() - task_context.start_time, upload_result.status_code, upload_result.hdfs_path_id))
                checksum_resource_uri = "hsink/fileresource/files/%s/digest/sha-256" % upload_result.hdfs_path_id
                tl.addinfo("Verifying checksum at %s" % (checksum_resource_uri))
                hdfs_sha256_checksum = hdfs_rest_client.get_string(checksum_resource_uri)
                if ChecksumFile(aip_path).get(ChecksumAlgorithm.SHA256) == hdfs_sha256_checksum:
                    tl.addinfo("Checksum verification completed, the package was transmitted successfully.")
                else:
                    tl.adderr("Checksum verification failed, an error occurred while trying to transmit the package.")
        except Exception, err:
            tl.adderr("An error occurred: %s" % err)
        task_context.task_status = 1 if (len(tl.err) > 0) else 0
        return task_context.additional_data



class AIPtoDIPReset(DefaultTask):

    accept_input_from = ['All']

    def run_task(self, task_context):
        """
        SIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:12,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'AIPtoDIPReset'

        # create working directory if it does not exist
        if not os.path.exists(task_context.path):
            fileutils.mkdir_p(task_context.path)

        #remove and recreate empty directories
        data_path = os.path.join(task_context.path, "data")
        if os.path.exists(data_path):
            shutil.rmtree(data_path)
        mkdir_p(data_path)
        task_context.task_logger.addinfo("New empty 'data' directory created")

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
            task_context.task_logger.addinfo("Extracted SIP folder '%s' removed" % tar_base_name)

        # success status
        task_context.task_status = 0
        return #{'identifier': ""}


class DIPAcquireAIPs(DefaultTask):

    accept_input_from = ['All', AIPtoDIPReset.__name__]

    def run_task(self, task_context):
        """
        SIP Validation
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:13,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'DIPAcquireAIPs'

        tl = task_context.task_logger

        try:
            # create dip working directory
            if not os.path.exists(task_context.path):
                os.mkdir(task_context.path)

            selected_aips = task_context.additional_data["selected_aips"]
            # packagename is identifier of the DIP creation process
            #dip = DIP.objects.get(name=task_context.task_name)
            print "selected AIPs: %s" % selected_aips

            total_bytes_read = 0
            aip_total_size = 0
            for aip_source in selected_aips.values():
                if not os.path.exists(aip_source):
                    tl.adderr("Missing AIP source %s" % aip_source)
                    tl.adderr("Task failed %s" % task_context.uuid)
                    task_context.task_status = 1
                    return
                else:
                    aip_total_size+=fsize(aip_source)

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
            task_context.task_status = 1
        return


class DIPExtractAIPs(DefaultTask):

    accept_input_from = ['All', DIPAcquireAIPs.__name__, "DIPExtractAIPs"]

    def run_task(self, task_context):
        """
        DIP Extract AIPs
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:14,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        #task_context.event_type = 'DIPExtractAIPs'

        tl = task_context.task_logger

        try:
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            # create dip working directory
            if not os.path.exists(task_context.path):
                os.mkdir(task_context.path)

            # packagename is identifier of the DIP creation process
            #dip = DIP.objects.get(name = ip.packagename)
            selected_aips = task_context.additional_data["selected_aips"]

            total_members = 0
            for aip_identifier, aip_source in selected_aips.iteritems():
                if not os.path.exists(aip_source):
                    tl.adderr("Missing AIP source %s" % aip_source)
                    tl.adderr("Task failed %s" % task_context.uuid)
                    task_context.task_status = 1
                    return
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
                # ip.statusprocess = tc.success_status
                # ip.save()
                tl.addinfo("Untar of %d items from package %s finished" % (current_package_total_members, aip_identifier))
            tl.addinfo(("Untar of %d items in total finished" % total_processed_members))
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            task_context.task_status = 0
        except Exception as e:
            tl.adderr("Task failed %s" % task_context.uuid)
            tl.adderr("Task failed %s" % e.message)
            task_context.task_status = 1
            pass

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
        @param      tc: order:15,type:4,stage:4
        """

        # Add the event type - will be put into Premis.
        task_context.event_type = 'DIPImportSIARD'

        tl = task_context.task_logger

        try:
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')

            # create dip working directory
            #if not os.path.exists(task_context.path):
            #    os.mkdir(task_context.path)


            dbptk='/home/bartham/siard/dbptk-app-2.0.0-beta3.2.5.jar'
            db_user = 'root'
            db_passwd='arkiv'
            db_type = 'mysql'
            db_host = 'localhost'
            # find SIARD2 file in working dir
            for root, dirs, files in os.walk(task_context.path):
                for file in files:
                    if file.endswith(".siard2"):
                        siard_path = os.path.join(root, file)
                        print siard_path
                        db_name = os.path.splitext(file)[0]

                        print "Database name: %s" % db_name
                        # drop database if existing
                        command = [
                            'mysql',
                            'mysql',
                            '-u', db_user,
                            '-p%s' % db_passwd,
                            '-e', 'DROP DATABASE IF EXISTS %s;' % db_name,
                            ]
                        runCommand(command)
                        # create database
                        command = [
                            'mysql',
                            'mysql',
                            '-u', db_user,
                            '-p%s' % db_passwd,
                            '-e', 'CREATE DATABASE IF NOT EXISTS %s;' % db_name,
                            ]
                        runCommand(command)
                        # import file to database
                        command = [
                            'java', '-jar', dbptk, '-i', 'siard-2', '-if', siard_path, '-e', db_type, '-eh', db_host, '-edb', db_name, '-eu', db_user, '-ep', db_passwd,
                        ]
                        runCommand(command)
                        #java -jar $DBPTK -i siard-2 --import-file=world.siard2 -e mysql --export-hostname=localhost --export-database=world --export-user=$USER --export-password=$PASSWORD

        except Exception as e:
            tl.adderr("Task failed %s" % task_context.uuid)
            tl.adderr("Task failed %s" % e.message)
            task_context.task_status = 1
            pass

        task_context.task_status = 0
