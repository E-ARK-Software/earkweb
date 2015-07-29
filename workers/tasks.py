from celery import Task, shared_task
import time, logging
from sip2aip.models import MyModel
from time import sleep
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
