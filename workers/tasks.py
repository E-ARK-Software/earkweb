from celery import Task, shared_task
import time, logging, os
from sip2aip.models import MyModel
from time import sleep
from config import params
from celery import current_task
from earkcore.utils import fileutils
from earkcore.models import InformationPackage
from earkcore.utils import randomutils
from taskresult import TaskResult
from earkcore.packaging.extraction import Extraction

class SomeCreation(Task):
    def __init__(self):
        self.ignore_result = False

    def run(self, param1, *args, **kwargs):
        """
        This function creates something
        @type       param1: string
        @param      param1: First parameter
        @rtype:     string
        @return:    Parameter
        """
        return "Parameter: " + param1

class SimulateLongRunning(Task):

    def __init__(self):
        self.ignore_result = False

    def run(self, pk_id, *args, **kwargs):
        """
        This function creates something
        @type       pk_id: int
        @param      pk_id: Package id
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

class AssignIdentifier(Task):

    def __init__(self):
        self.ignore_result = False

    def valid_state(self, ip):
        err = []
        if not (ip.statusprocess == 0):
            err.append("Incorrect information package status")
        return  err

    def run(self, pk_id, *args, **kwargs):
        """
        Assign identifier
        @type       package_path: int
        @param      package_path: Primary key
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})
        log.append("AssignIdentifier task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)
        err = self.valid_state(ip)
        if len(err) > 0:
            return TaskResult(False, log, err)
        ip.statusprocess=100
        ip.uuid=randomutils.getUniqueID()
        ip.save()
        log.append("UUID %s assigned to package %s" % (ip.uuid, ip.path))
        self.update_state(state='PROGRESS',meta={'process_percent': 100})
        return TaskResult(True, log, err)

class ExtractTar(Task):

    def __init__(self):
        self.ignore_result = False

    def valid_state(self, ip):
        err = []
        if not (ip.statusprocess == 100):
            err.append("Incorrect information package status (must be 100)")
        if (ip.uuid is None or ""):
            err.append("UUID missing")
        target_dir = os.path.join(params.config_path_work, ip.uuid)
        if (os.path.exists(target_dir)):
            err.append("Directory already exists in working area")
        return err

    def run(self, pk_id, *args, **kwargs):
        """
        Unpack tar file to destination directory
        @type       package_path: int
        @param      package_path: Primary key
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []
        try:
            log.append("ExtractTar task %s" % current_task.request.id)
            ip = InformationPackage.objects.get(pk=pk_id)
            err = self.valid_state(ip)
            if len(err) > 0:
                return TaskResult(False, log, err)
            ip.statusprocess = 200
            ip.save()
            target_dir = os.path.join(params.config_path_work, ip.uuid)
            fileutils.mkdir_p(target_dir)
            extr = Extraction()
            result = extr.extract(ip.path, target_dir)
            return TaskResult(result.success, log+result.log, err+result.err)
        except Exception, err:
            return TaskResult(False, [], err)

class Reset(Task):

    def __init__(self):
        self.ignore_result = False

    def run(self, pk_id, *args, **kwargs):
        """
        Reset identifier and package status
        @type       package_path: int
        @param      package_path: Primary key
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        log = []
        err = []
        self.update_state(state='PROGRESS',meta={'process_percent': 50})

        log.append("ResetTask task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(pk=pk_id)

        ip.statusprocess = 0
        log.append("Setting statusprocess to 0")
        ip.uuid = ""
        log.append("Setting uuid to empty string")
        ip.save()
        self.update_state(state='PROGRESS',meta={'process_percent': 100})
        return TaskResult(True, log, err)
