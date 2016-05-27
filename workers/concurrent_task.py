# import os
import traceback

from celery import Task
# from celery import current_task

# from earkcore.metadata.premis.premisgenerator import PremisGenerator
# from tasklogger import TaskLogger
# from workers.ip_state import IpState

import logging
logger = logging.getLogger(__name__)


'''
ConcurrentTask is similar to DefaultTask. It omits everything that could lead to concurrency problems when executing a
lot of tasks in parallel. Such as:
* persisting the IP state (IP state will always be 0, even if this task fails)
* writing to log files
* creation/checking of paths of any kind
* updates to earkweb UI (progress)

If anything of this is desired, the concrete implementations have to take care of it.
'''


class ConcurrentTask(Task):

    # Only task specific constants should be defined here, each run method execution has its own task execution context.
    # Gets set by the implementation to indicate accepted output from other tasks
    accept_input_from = []
    # Task name is name of instantiating class (is set by the concrete task implementation)
    task_name = ""

    def __init__(self):
        self.task_name = str(self.__name__)

    def initialize(self, task_context):

        task_context.task_name = self.task_name

        return task_context

    def finalize(self, task_context):
        """
        THis task does nothing, since we don't log anything here.

        Finalize logging task. Can be called several times to get an updated result object.
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """

        return task_context

    def run_task(self, task_context):
        """
        This method is overriden by the task method implementation (thi one has type 0 in order to not be shown)
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:0,type:0,stage:0
        """
        # task_context.task_logger.addinfo("Executing default task (to be overridden)")
        task_context.task_status = 0
        return

    def run(self, task_context, *args, **kwargs):
        """
        Run method of celery task. This method will be executed by celery.
        This method calls the 'run_task' method which is overridden by the concrete task implementation.

        @type       uuid: str
        @param      uuid: Internal identifier

        @type       path: str
        @param      path: Path where the IP is stored

        @type       path: additional_params
        @param      path: Additional parameters dictionary (passed through from actual task implementation to celery result)

        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log, additional parameters)
        """

        # initialize task
        # logger.debug("Executing %s task." % self.task_name)
        task_context = self.initialize(task_context)
        try:
            # IP state is not checked, just execute actual task implementation; can return additional result parameters
            # in the dictionary additional_params. This dictionary is stored as part of the celery result
            # and is stored in the result backend (AsyncResult(task_id).result.add_res_parms).
            task_context.additional_data = self.run_task(task_context) # IMPORTANT: task has to return task_context.additional_data!
        except Exception, e:
            # We don't log anything, keep this in mind when debugging.
            # Also the task_context.task_status will still be 0.
            # task_context.task_logger.adderr("An error occurred: %s" % e)
            traceback.print_exc()
            task_context.task_status = 0
            pass

        return self.finalize(task_context)

    def can_connect(self, task):
        return task in self.accept_input_from
