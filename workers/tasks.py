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
# Start worker: celery --app=earkweb.celeryapp:app worker
# Example:
#     from workers.tasks import SomeCreation
#     result = SomeCreation().apply_async(('test',), queue='smdisk')
#     result.status
#     result.result

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

class OtherJob(Task):
    def __init__(self):
        self.ignore_result = False

    def run(self, param, *args, **kwargs):
        """
        This is another job
        @type       param: string
        @param      param: This task takes only one parameter
        @rtype:     string
        @return:    Parameter
        """
        return "Parameter: " + param

class AnotherJob(Task):
# Example:
#     from workers.tasks import SomeCreation
#     result = SomeCreation().apply_async(('test',), queue='smdisk')
#     result.status
#     result.result
    def __init__(self):
        self.ignore_result = False

    def run(self, param, *args, **kwargs):
        """
        This is another job
        @type       param: string
        @param      param: This task takes only one parameter
        @rtype:     string
        @return:    Parameter
        """
        return "Parameter: " + param

class SimulateLongRunning(Task):

    def __init__(self):
        self.ignore_result = False

    def run(self, factor, *args, **kwargs):
        """
        This function creates something
        @type       param1: int
        @param      param1: Factor
        @rtype:     string
        @return:    Parameter
        """
        for i in range(1, factor):
          fn = 'Fn %s' % i
          ln = 'Ln %s' % i
          my_model = MyModel(fn=fn, ln=ln)
          my_model.save()

          process_percent = int(100 * float(i) / float(factor))

          sleep(0.1)
          self.update_state(state='PROGRESS',meta={'process_percent': process_percent})

        return True

class AssignIdentifier(Task):

    log = []
    err = []

    def __init__(self):
        self.ignore_result = False

    def valid_state(self, ip):
        if not (ip.statusprocess == 0):
            self.err.append("Incorrect information package status")
        return (len(self.err) == 0)

    def run(self, package_path, *args, **kwargs):
        """
        Unpack tar file to destination directory
        @type       package_path: string
        @param      package_path: Path to package to be unpackaged
        @rtype:     boolean
        @return:    success/failure of the unpackaging process
        """
        self.log.append("AssignIdentifier task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(path=package_path)
        if not self.valid_state(ip):
            return TaskResult(False, self.log, self.err)
        ip.statusprocess=100
        ip.uuid=randomutils.getUniqueID()
        ip.save()
        self.log.append("UUID %s assigned to package %s" % (ip.uuid, package_path))
        return TaskResult(True, self.log, [])

class ExtractTar4(Task):

    log = []
    err = []

    def __init__(self):
        self.ignore_result = False

    def valid_state(self, ip):
        if not (ip.statusprocess == 100):
            self.err.append("Incorrect information package status")
        if (ip.uuid is None or ""):
            self.err.append("UUID missing")
        target_dir = os.path.join(params.config_path_work, ip.uuid)
        if (os.path.exists(target_dir)):
            self.err.append("Directory already exists in working area")
        return (len(self.err) == 0)

    def run(self, uuid, *args, **kwargs):
        """
        Unpack tar file to destination directory
        @type       package_path: string
        @param      package_path: Path to package to be unpackaged
        @rtype:     boolean
        @return:    success/failure of the unpackaging process
        """
        self.log.append("ExtractTar task %s" % current_task.request.id)
        ip = InformationPackage.objects.get(uuid=uuid)
        if not self.valid_state(ip):
            return TaskResult(False, self.log, self.err)
        ip.statusprocess = 200
        ip.save()
        target_dir = os.path.join(params.config_path_work, ip.uuid)
        fileutils.mkdir_p(target_dir)
        extr = Extraction()
        result = extr.extract(ip.path, target_dir)
        self.log.append(result.log)
        self.err.append(result.err)
        return TaskResult(True, self.log, self.err)
