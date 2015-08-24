from celery import Task, shared_task
import time, os
from sip2aip.models import MyModel
from time import sleep
from config import params
from celery import current_task
from earkcore.utils import fileutils
from earkcore.models import InformationPackage
from earkcore.utils import randomutils
from earkcore.xml.validationresult import ValidationResult
from earkcore.xml.deliveryvalidation import DeliveryValidation
from taskresult import TaskResult
from earkcore.packaging.extraction import Extraction
import tarfile
import logging
logger = logging.getLogger(__name__)
import traceback
from workers.statusvalidation import StatusValidation
from earkcore.metadata.mets.MetsValidation import MetsValidation
from earkcore.metadata.mets.ParsedMets import ParsedMets
import shutil

class SimulateLongRunning(Task):

    def __init__(self):
        self.ignore_result = False

    def run(self, pk_id, tc, *args, **kwargs):
        """
        This function creates something
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:-1,success_status:-1,error_status:-1
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        factor = 1000
        for i in range(1, factor):
          fn = 'Fn %s' % i
          ln = 'Ln %s' % i
          my_model = MyModel(fn=fn, ln=ln)
          my_model.save()

          process_percent = int(100 * float(i) / float(factor))

          sleep(0.1)
          self.update_state(state='PROGRESS',meta={'process_percent': process_percent})

        return TaskResult(True, ['Long running process finished'], [])

class Reset(Task):

    def __init__(self):
        self.ignore_result = False

    def run(self, pk_id, tc, *args, **kwargs):
        """
        Reset identifier and package status
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:-1,success_status:0,error_status:90
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []
        err = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})

        log.append("ResetTask task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)
        ip.statusprocess = tc.success_status
        log.append("Setting statusprocess to 0")
        ip.uuid = ""
        log.append("Setting uuid to empty string")
        ip.save()
        self.update_state(state='PROGRESS',meta={'process_percent': 100})
        return TaskResult(True, log, err)

class AssignIdentifier(Task, StatusValidation):

    def run(self, pk_id, tc, *args, **kwargs):
        """
        Assign identifier
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:100,success_status:200,error_status:290
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})
        log.append("AssignIdentifier task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)
        err = self.valid_state(ip, tc)
        if len(err) > 0:
            return TaskResult(False, log, err)
        ip.statusprocess=tc.success_status
        ip.uuid=randomutils.getUniqueID()
        ip.save()
        log.append("UUID %s assigned to package %s" % (ip.uuid, ip.path))
        self.update_state(state='PROGRESS',meta={'process_percent': 100})
        return TaskResult(True, log, err)

class SIPDeliveryValidation(Task):

    def __init__(self):
        self.ignore_result = False

    def valid_state(self, ip, tc, delivery_file, schema_file, package_file):
        err = []
        # if ip.statusprocess != tc.expected_status:
        #     err.append("Incorrect information package status (must be %d)" % tc.expected_status)
        if not os.path.exists(delivery_file):
            err.append("Delivery file does not exist: %s" % delivery_file)
        if not os.path.exists(schema_file):
            err.append("Schema file does not exist: %s" % schema_file)
        if not os.path.exists(package_file):
            err.append("Package file does not exist: %s" % package_file)
        return  err

    def run(self, pk_id, tc, *args, **kwargs):
        """
        SIP Delivery Validation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:0,success_status:100,error_status:190
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []; err = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})
        log.append("SIPDeliveryValidation task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)
        filename, file_ext = os.path.splitext(ip.path)
        delivery_dir = params.config_path_reception
        delivery_file = "%s.xml" % filename
        # package name is basename of delivery package
        ip.packagename = os.path.basename(filename)
        schema_file = os.path.join(delivery_dir, 'IP_CS_mets.xsd')
        package_file = ip.path

        err = self.valid_state(ip, tc, delivery_file, schema_file, package_file)
        if len(err) > 0:
            return TaskResult(False, log, err)

        try:
            sdv = DeliveryValidation()
            validation_result = sdv.validate_delivery(delivery_dir, delivery_file, schema_file, package_file)
            log = log + validation_result.log
            err = err + validation_result.err
            log.append("Delivery validation result (xml/file size/checksum): %s" % validation_result.valid)
            logger.info(str(validation_result))
            ip.statusprocess = tc.success_status if validation_result.valid else tc.error_status;
            ip.save()
            self.update_state(state='PROGRESS',meta={'process_percent': 100})
            return TaskResult(validation_result.valid, log, err)
        except Exception, err:
            tb = traceback.format_exc()
            logger.error(str(tb))
            return TaskResult(False, [], ['An error occurred: '+str(tb)])

class ExtractTar(Task):

    def __init__(self):
        self.ignore_result = False

    def valid_state(self, ip, tc):
        err = []
        if ip.statusprocess != tc.expected_status:
            err.append("Incorrect information package status (must be %d)" % tc.expected_status)
        if (ip.uuid is None or ""):
            err.append("UUID missing")
        target_dir = os.path.join(params.config_path_work, ip.uuid)
        if (os.path.exists(target_dir)):
            err.append("Directory already exists in working area")
        return err

    def run(self, pk_id, tc, *args, **kwargs):
        """
        Unpack tar file to destination directory
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:200,success_status:300,error_status:390
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []
        err = []
        ip = InformationPackage.objects.get(pk=pk_id)
        try:
            log.append("ExtractTar task %s" % current_task.request.id)
            logger.info("ExtractTar task %s" % current_task.request.id)
            err = self.valid_state(ip, tc)
            if len(err) > 0:
                logger.error("Errors: "+(str(err)))
                return TaskResult(False, log, err)
            err = self.valid_state(ip, tc)
            target_dir = os.path.join(params.config_path_work, ip.uuid)
            fileutils.mkdir_p(target_dir)
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')
            tar_object = tarfile.open(name=ip.path, mode='r', encoding='utf-8')
            members = tar_object.getmembers()
            total = len(members)
            i = 0; perc = 0
            for member in members:
                if i % 10 == 0:
                    perc = (i*100)/total
                    logger.info("Status: %s" % str(perc))
                    self.update_state(state='PROGRESS',meta={'process_percent': perc})
                tar_object.extract(member, target_dir)
                i += 1
            ip.statusprocess = tc.success_status
            ip.save()
            self.update_state(state='PROGRESS',meta={'process_percent': 100})
            logger.info("Extraction of %d items finished" % total)
            log.append("Extraction of %d items finished" % total)
            return TaskResult(True, log, err)
        except Exception, err:
            ip.statusprocess = tc.error_status
            ip.save()
            tb = traceback.format_exc()
            logger.error(str(tb))
            return TaskResult(False, [], ['An error occurred: '+str(tb)])

class SIPValidation(Task, StatusValidation):

    def run(self, pk_id, tc, *args, **kwargs):
        """
        SIP Structure Validation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:300,success_status:400,error_status:490
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []; err = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})
        log.append("SIPStructureValidation task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)

        err = self.valid_state(ip, tc)
        if len(err) > 0:
            return TaskResult(False, log, err)

        def checkFile(descr, f):
            if os.path.exists(f):
                log.append("%s found: %s" % (descr, os.path.abspath(f)))
            else:
                err.append("%s missing: %s" % (descr, os.path.abspath(f)) )

        try:

            ip_work_dir = os.path.join(params.config_path_work, ip.uuid)
            checkFile("SIP METS file", os.path.join(ip_work_dir, ip.packagename, "IP.xml"))
            checkFile("Content directory", os.path.join(ip_work_dir, ip.packagename, "Content"))
            checkFile("Metadata directory", os.path.join(ip_work_dir, ip.packagename, "Metadata"))

            mets_file = os.path.join(ip_work_dir, ip.packagename, "IP.xml")
            parsed_mets = ParsedMets(os.path.join(ip_work_dir, ip.packagename))
            parsed_mets.load_mets(mets_file)
            mval = MetsValidation(parsed_mets)
            size_val_result = mval.validate_files_size()
            log += size_val_result.log
            err += size_val_result.err

            valid = (len(err) == 0)

            ip.statusprocess = tc.success_status if valid else tc.error_status;
            ip.save()
            self.update_state(state='PROGRESS',meta={'process_percent': 100})
            return TaskResult(valid, log, err)
        except Exception, err:
            tb = traceback.format_exc()
            logger.error(str(tb))
            return TaskResult(False, log, ['An error occurred: '+str(tb)])

class AIPStructure(Task, StatusValidation):

    def run(self, pk_id, tc, *args, **kwargs):
        """
        SIP Structure Validation
        @type       pk_id: int
        @param      pk_id: Primary key
        @type       tc: TaskConfig
        @param      tc: expected_status:-1,success_status:-1,error_status:-1
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []; err = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})
        log.append("SIPStructureValidation task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)

        err = self.valid_state(ip, tc)
        if len(err) > 0:
            return TaskResult(False, log, err)

        def checkFile(descr, f):
            if os.path.exists(f):
                log.append("%s found: %s" % (descr, os.path.abspath(f)))
            else:
                err.append("%s missing: %s" % (descr, os.path.abspath(f)) )

        try:

            ip_work_dir = os.path.join(params.config_path_work, ip.uuid)
            src = os.path.join(ip_work_dir, ip.packagename)
            dest = os.path.join(ip_work_dir, "submission", ip.packagename)
            shutil.move(src, dst)

            # create root mets



            valid = True

            ip.statusprocess = tc.success_status if valid else tc.error_status;
            ip.save()
            self.update_state(state='PROGRESS',meta={'process_percent': 100})
            return TaskResult(valid, log, err)
        except Exception, err:
            tb = traceback.format_exc()
            logger.error(str(tb))
            return TaskResult(False, log, ['An error occurred: '+str(tb)])

