from celery import Task, shared_task
import time, os
from sip2aip.models import MyModel
from time import sleep
from config import params
from config.config import root_dir
from celery import current_task
from earkcore.utils import fileutils
from earkcore.models import InformationPackage
from earkcore.utils import randomutils
from earkcore.xml.deliveryvalidation import DeliveryValidation
from taskresult import TaskResult
import tarfile
import traceback
from workers.statusvalidation import StatusValidation
from earkcore.metadata.mets.MetsValidation import MetsValidation
from earkcore.metadata.mets.ParsedMets import ParsedMets
from earkcore.metadata.mets.MetsManipulate import Mets
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm
from earkcore.metadata.premis.PremisManipulate import Premis
import shutil
from earkcore.utils.fileutils import increment_file_name_suffix
from earkcore.utils.fileutils import latest_aip
from tasklogger import TaskLogger
from os import walk
import logging
from earkcore.rest.restendpoint import RestEndpoint
from earkcore.rest.hdfsrestclient import HDFSRestClient
from functools import partial
from statusvalidation import check_status
from search.models import DIP, AIP, Inclusion
from earkcore.filesystem.chunked import FileBinaryDataChunks
from earkcore.filesystem.fsinfo import fsize
from earkcore.fixity.ChecksumFile import ChecksumFile
from earkcore.fixity.tasklib import check_transfer

def custom_progress_reporter(task, percent):
    task.update_state(state='PROGRESS', meta={'process_percent': percent})

def init_task(pk_id, task_name, task_logfile_name):
    start_time = time.time()
    ip = InformationPackage.objects.get(pk=pk_id)
    if not ip.uuid:
        ip.uuid = randomutils.getUniqueID()
    ip_work_dir = os.path.join(params.config_path_work, ip.uuid)
    task_log_file_dir = os.path.join(ip_work_dir, 'metadata')
    task_log_file = os.path.join(task_log_file_dir, "%s.log" % task_logfile_name)
    # create working directory
    if not os.path.exists(ip_work_dir):
        os.mkdir(ip_work_dir)
    # create log directory
    if not os.path.exists(task_log_file_dir):
        os.mkdir(task_log_file_dir)
    tl = TaskLogger(task_log_file)
    tl.addinfo(("%s task %s" % (task_name, current_task.request.id)))
    return ip, ip_work_dir, tl, start_time


def handle_error(ip, tc, tl):
    ip.statusprocess = tc.error_status
    ip.save()
    tb = traceback.format_exc()
    tl.adderr(("An error occurred: %s" % str(tb)))
    logging.error(tb)
    return tl.fin()


class Reset(Task):
    def __init__(self):
        self.ignore_result = False

    def run(self, pk_id, tc, *args, **kwargs):
        """
        Reset identifier and package status
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:0,expected_status:status!=-9999,success_status:0,error_status:90
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        tl = TaskLogger(None)
        tl.addinfo("ResetTask task %s" % current_task.request.id)
        self.update_state(state='PROGRESS', meta={'process_percent': 1})

        ip = InformationPackage.objects.get(pk=pk_id)

        filename, file_ext = os.path.splitext(ip.path)
        packagename = os.path.basename(filename)

        temporary_working_dir = os.path.join(params.config_path_work, packagename)
        if packagename != "" and os.path.exists(temporary_working_dir):
            tl.addinfo("Temporary package directory removed from working directory: " + temporary_working_dir)
            shutil.rmtree(temporary_working_dir)
        ip.statusprocess = tc.success_status
        tl.addinfo("Setting statusprocess to 0")
        ip.uuid = ""
        tl.addinfo("Setting uuid to empty string")
        ip.identifier = ""
        tl.addinfo("Setting identifier to empty string")
        ip.packagename = ""
        tl.addinfo("Setting packagename to empty string")
        ip.save()

        self.update_state(state='PROGRESS', meta={'process_percent': 100})
        return tl.fin()


class SIPDeliveryValidation(Task):

    def valid_state(self, ip, tc, delivery_file, schema_file, package_file):
        err = []
        check_status(ip.statusprocess, tc.expected_status, err)
        if not os.path.exists(delivery_file):
            err.append("Delivery file does not exist: %s" % delivery_file)
        if not os.path.exists(schema_file):
            err.append("Schema file does not exist: %s" % schema_file)
        if not os.path.exists(package_file):
            err.append("Package file does not exist: %s" % package_file)
        return err

    def run(self, pk_id, tc, *args, **kwargs):
        """
        SIP Delivery Validation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:1,expected_status:status==0,success_status:100,error_status:190
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "SIPDeliveryValidation", "sip_to_aip_processing")
        tl.addinfo(("New UUID assigned: %s" % ip.uuid))
        try:
            self.update_state(state='PROGRESS', meta={'process_percent': 1})
            filename, file_ext = os.path.splitext(ip.path)
            delivery_dir = params.config_path_reception
            delivery_file = "%s.xml" % filename
            # package name is basename of delivery package
            ip.packagename = os.path.basename(filename)
            schema_file = os.path.join(delivery_dir, 'IP_CS_mets.xsd')
            package_file = ip.path
            self.update_state(state='PROGRESS', meta={'process_percent': 10})
            # create minimal premis file to record initial actions
            # with open(root_dir+'/earkresources/PREMIS_skeleton.xml', 'r') as premis_file:
            #     my_premis = Premis(premis_file)
            # my_premis.add_object(os.path.basename(ip.path))
            # my_premis.add_agent('earkweb')
            # my_premis.add_event('SIP Delivery Validation', 'earkweb')
            #
            # path_premis = os.path.join(temporary_working_dir,'PREMIS.xml')
            # with open(path_premis, 'w') as output_file:
            #     output_file.write(my_premis.to_string())
            tl.err = self.valid_state(ip, tc, delivery_file, schema_file, package_file)
            if len(tl.err) > 0:
                return tl.fin()
            sdv = DeliveryValidation()
            self.update_state(state='PROGRESS', meta=dict(process_percent=50))
            validation_result = sdv.validate_delivery(delivery_dir, delivery_file, schema_file, package_file)
            self.update_state(state='PROGRESS', meta={'process_percent': 90})
            tl.log = tl.log + validation_result.log
            tl.err = tl.err + validation_result.err
            tl.addinfo("Delivery validation result (xml/file size/checksum): %s" % validation_result.valid)
            ip.statusprocess = tc.success_status if validation_result.valid else tc.error_status
            ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            return tl.fin()
        except Exception:
            return handle_error(ip, tc, tl)


class IdentifierAssignment(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        Assign identifier
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:2,expected_status:status==100,success_status:200,error_status:290
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "IdentifierAssignment", "sip_to_aip_processing")
        self.update_state(state='PROGRESS', meta={'process_percent': 1})
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()
        ip.statusprocess = tc.success_status
        ip.identifier = randomutils.getUniqueID()
        ip.save()
        tl.addinfo("Identifier %s assigned to package %s" % (ip.identifier, ip.path))
        self.update_state(state='PROGRESS', meta={'process_percent': 100})
        return tl.fin()


class SIPExtraction(Task):
    def valid_state(self, ip, tc):
        err = []
        check_status(ip.statusprocess, tc.expected_status, err)
        if ip.uuid is None or "":
            err.append("UUID missing")
        target_dir = os.path.join(params.config_path_work, ip.uuid)
        return err

    def run(self, pk_id, tc, *args, **kwargs):
        """
        Unpack tar file to destination directory
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:3,expected_status:status==200,success_status:300,error_status:390
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "SIPExtraction", "sip_to_aip_processing")
        try:
            tl.addinfo(("ExtractTar task %s" % current_task.request.id))
            tl.err = self.valid_state(ip, tc)
            if len(tl.err) > 0:
                return tl.fin()
            target_dir = os.path.join(params.config_path_work, ip.uuid)
            fileutils.mkdir_p(target_dir)
            import sys

            reload(sys)
            sys.setdefaultencoding('utf8')
            tar_object = tarfile.open(name=ip.path, mode='r', encoding='utf-8')
            members = tar_object.getmembers()
            total = len(members)
            i = 0
            perc = 0
            for member in members:
                if i % 10 == 0:
                    perc = (i * 100) / total
                    self.update_state(state='PROGRESS', meta={'process_percent': perc})
                tar_object.extract(member, target_dir)
                tl.addinfo(("File extracted: %s" % member.name), display=False)
                i += 1
            ip.statusprocess = tc.success_status
            ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            tl.addinfo(("Extraction of %d items finished" % total))
            return tl.fin()
        except Exception, err:
            return handle_error(ip, tc, tl)


class SIPValidation(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        SIP Structure Validation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:4,expected_status:status>=300~and~status<400,success_status:400,error_status:490
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "SIPValidation", "sip_to_aip_processing")
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()

        def check_file(descr, f):
            if os.path.exists(f):
                tl.addinfo("%s found: %s" % (descr, os.path.abspath(f)))
            else:
                tl.adderr(("%s missing: %s" % (descr, os.path.abspath(f))))

        try:
            ip_work_dir = os.path.join(params.config_path_work, ip.uuid)
            check_file("SIP METS file", os.path.join(ip_work_dir, ip.packagename, "METS.xml"))
            check_file("Content directory", os.path.join(ip_work_dir, ip.packagename, "Content"))
            check_file("Metadata directory", os.path.join(ip_work_dir, ip.packagename, "Metadata"))
            mets_file = os.path.join(ip_work_dir, ip.packagename, "METS.xml")
            parsed_mets = ParsedMets(os.path.join(ip_work_dir, ip.packagename))
            parsed_mets.load_mets(mets_file)
            mval = MetsValidation(parsed_mets)
            size_val_result = mval.validate_files_size()
            tl.log += size_val_result.log
            tl.err += size_val_result.err
            valid = (len(tl.err) == 0)
            ip.statusprocess = tc.success_status if valid else tc.error_status
            ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            return tl.fin()
        except Exception, err:
            return handle_error(ip, tc, tl)


class AIPCreation(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        AIP Structure creation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:5,expected_status:status==400,success_status:500,error_status:590
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "AIPCreation", "sip_to_aip_processing")
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()
        try:
            package_dir = os.path.join(ip_work_dir, ip.packagename)
            submission_dir = os.path.join(ip_work_dir, "submission")
            package_in_submission_dir = os.path.join(submission_dir, ip.packagename)
            shutil.move(package_dir, package_in_submission_dir)
            tl.addinfo("Package directory %s moved to submission directory %s" % (package_dir, package_in_submission_dir))

            # create submission mets
            mets_skeleton_file = root_dir + '/earkresources/METS_skeleton.xml'
            with open(mets_skeleton_file, 'r') as mets_file:
                submission_mets_file = Mets(wd=ip_work_dir, alg=ChecksumAlgorithm.SHA256)
            # my_mets.add_dmd_sec('EAD', 'file://./metadata/EAD.xml')
            admids = []
            # admids.append(my_mets.add_tech_md('file://./metadata/PREMIS.xml#Obj'))
            # admids.append(my_mets.add_digiprov_md('file://./metadata/PREMIS.xml#Ingest'))
            # admids.append(my_mets.add_rights_md('file://./metadata/PREMIS.xml#Right'))
            submission_mets_file.add_file_grp(['submission'])
            rel_path_mets = "file://./submission/%s/%s" % (ip.packagename, "METS.xml")
            submission_mets_file.add_file(['submission'], rel_path_mets, admids)
            submission_mets_file.root.set('TYPE', 'AIP')
            path_mets = os.path.join(submission_dir, "METS.xml")
            with open(path_mets, 'w') as output_file:
                output_file.write(submission_mets_file.to_string())
            tl.addinfo(("Submission METS file created: %s" % rel_path_mets))
            valid = True
            ip.statusprocess = tc.success_status if valid else tc.error_status
            ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            return tl.fin()
        except Exception:
            return handle_error(ip, tc, tl)


class AIPValidation(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        AIPValidation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:6,expected_status:status>=500,success_status:600,error_status:690
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "AIPValidation", "sip_to_aip_processing")
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()

        try:
            tl.addinfo("AIP always validates, this task is not implemented yet")
            valid = True # TODO: Implement AIP validation
            ip.statusprocess = tc.success_status if valid else tc.error_status
            ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            return tl.fin()
        except Exception, err:
            return handle_error(ip, tc, tl)


class AIPPackaging(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        AIP Structure creation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:7,expected_status:status>=600,success_status:700,error_status:790
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "AIPPackaging", "sip_to_aip_processing")
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()
        try:
            # identifier (not uuid of the working directory) is used as first part of the tar file
            ip_storage_dir = os.path.join(params.config_path_storage, ip.identifier)
            import sys

            reload(sys)
            sys.setdefaultencoding('utf8')
            # append generation number to tar file; if tar file exists, the generation number is incremented
            storage_tar_file = increment_file_name_suffix(ip_storage_dir, "tar")
            tar = tarfile.open(storage_tar_file, "w:")
            tl.addinfo("Packaging working directory: %s" % ip_work_dir)
            total = sum([len(files) for (root, dirs, files) in walk(ip_work_dir)])
            tl.addinfo("Total number of files in working directory %d" % total)
            # log file is closed at this point because it will be included in the package,
            # subsequent log messages can only be shown in the gui
            tl.fin()
            i = 0
            for subdir, dirs, files in os.walk(ip_work_dir):
                for file in files:
                    entry = os.path.join(subdir, file)
                    tar.add(entry)
                    if i % 10 == 0:
                        perc = (i * 100) / total
                        self.update_state(state='PROGRESS', meta={'process_percent': perc})
                    i += 1
            tar.close()
            tl.log.append("Package stored: %s" % storage_tar_file)
            result = tl.fin()
            ip.statusprocess = tc.success_status if result.success else tc.error_status
            ip.save()
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            return result
        except Exception, err:
            return handle_error(ip, tc, tl)


class LilyHDFSUpload(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        AIP Structure creation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:8,expected_status:status>=700,success_status:800,error_status:890
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "LilyHDFSUpload", None)
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()
        try:
            # identifier (not uuid of the working directory) is used as first part of the tar file
            ip_storage_dir = os.path.join(params.config_path_storage, ip.identifier)
            aip_path = latest_aip(ip_storage_dir, 'tar')

            tl.addinfo("Start uploading AIP %s from local path: %s" % (ip.identifier, aip_path))

            if aip_path is not None:

                # Reporter function which will be passed via the HDFSRestClient to the FileBinaryDataChunks.chunks()
                # method where the actual reporting about the upload progress occurs.


                rest_endpoint = RestEndpoint("http://81.189.135.189", "dm-hdfs-storage")
                tl.addinfo("Using REST endpoint: %s" % (rest_endpoint.to_string()))

                # Partial application of the custom_progress_reporter function so that the task object
                # is known to the FileBinaryDataChunks.chunks() method.
                partial_custom_progress_reporter = partial(custom_progress_reporter, self)
                hdfs_rest_client = HDFSRestClient(rest_endpoint, partial_custom_progress_reporter)
                rest_resource_path = "hsink/fileresource/files/{0}"

                upload_result = hdfs_rest_client.upload_to_hdfs(aip_path, rest_resource_path)
                tl.addinfo("Upload finished in %d seconds with status code %d: %s" % (time.time() - start_time, upload_result.status_code, upload_result.hdfs_path_id))
                result = tl.fin()
                ip.statusprocess = tc.success_status if result.success else tc.error_status
                ip.save()
                return result
            else:
                tl.adderr("No AIP file found for identifier: %s" % ip.identifier)
                return tl.fin()
        except Exception:
            return handle_error(ip, tc, tl)


class DIPAcquireAIPs(Task, StatusValidation):
    def run(self, pk_id, tc, *args, **kwargs):
        """
        AIP Structure creation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: order:9,expected_status:status==10000,success_status:10000,error_status:10000
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        ip, ip_work_dir, tl, start_time = init_task(pk_id, "DIPAcquireAIPs", "sip_to_aip_processing")
        tl.err = self.valid_state(ip, tc)
        if len(tl.err) > 0:
            return tl.fin()
        try:
            # create dip working directory
            if not os.path.exists(ip_work_dir):
                os.mkdir(ip_work_dir)

            # packagename is identifier of the DIP creation process
            dip = DIP.objects.get(name=ip.packagename)

            total_bytes_read = 0
            if dip.all_aips_available():
                dip_aips_total_size = dip.aips_total_size()
                tl.addinfo("DIP: %s, total size: %d" % (ip.packagename, dip_aips_total_size))
                for aip in dip.aips.all():

                    partial_custom_progress_reporter = partial(custom_progress_reporter, self)
                    package_extension = aip.source.rpartition('.')[2]
                    aip_in_dip_work_dir = os.path.join(ip_work_dir, ("%s.%s" % (aip.identifier, package_extension)))
                    tl.addinfo("Source: %s (%d)" % (aip.source, aip.source_size()))
                    tl.addinfo("Target: %s" % (aip_in_dip_work_dir))
                    with open(aip_in_dip_work_dir, 'wb') as target_file:
                        for chunk in FileBinaryDataChunks(aip.source, 65536, partial_custom_progress_reporter).chunks(total_bytes_read, dip_aips_total_size):
                            target_file.write(chunk)
                        if len(tl.err) > 0:
                            return tl.fin()
                        total_bytes_read += aip.source_size()
                        target_file.close()
                    check_transfer(aip.source, aip_in_dip_work_dir, tl)
                self.update_state(state='PROGRESS', meta={'process_percent': 100})
            result = tl.fin()
            ip.statusprocess = tc.success_status if result.success else tc.error_status
            ip.save()
            return result
        except Exception:
            return handle_error(ip, tc, tl)

