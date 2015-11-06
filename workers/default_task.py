import time
import os
import traceback

from celery import Task

from celery import current_task

from taskresult import TaskResult
from workers.default_task_context import DefaultTaskContext
from workers.ip_state import IpState
from tasklogger import TaskLogger
from earkcore.metadata.premis.PremisManipulate import Premis


class DefaultTask(Task):

    # Only task specific constants should be defined here, each run method execution has its own task execution context.
    # Gets set by the implementation to indicate accepted output from other tasks
    accept_input_from = []
    # Task name is name of instantiating class (is set by the concrete task implementation)
    task_name = ""

    # premis_manipulate = ""

    def __init__(self):
        self.task_name = str(self.__name__)

    def initialize(self, uuid, path):
        # create directories if they do not exist
        if not os.path.exists(path):
            os.mkdir(path)
        metadata_dir = os.path.join(path, 'metadata')
        if not os.path.exists(metadata_dir):
            os.mkdir(metadata_dir)

        # task logger
        task_log_file = os.path.join(metadata_dir, "%s.log" % "earkweb")
        tl = TaskLogger(task_log_file)
        tl.addinfo(("%s task %s" % (self.task_name, current_task.request.id)))
        tl.addinfo("Processing package %s" % uuid)
        self.update_state(state='PROGRESS', meta={'process_percent': 1})

        # create PREMIS file or return handle to task
        # premis_manipulate = None
        # path_premis = os.path.join(metadata_dir, 'PREMIS.xml')
        # if os.path.isfile(path_premis):
        #     premis_file = open(path_premis, 'rw')
        #     self.package_premis = Premis(premis_file)
        # else:
        #     package_premis = Premis()
        #     package_premis.add_agent('eark-aip-creation')
        #     with open(path_premis, 'w') as output_file:
        #          output_file.write(package_premis.to_string())
        #     premis_file = open(path_premis, 'rw')
        #     self.package_premis = Premis(premis_file)

        # get state, try reading current state from state.xml, otherwise set default to is error state,
        # which must then be set to success state explicitely.
        ip_state_doc_path = os.path.join(path, "state.xml")
        if os.path.exists(ip_state_doc_path):
            ip_state_xml = IpState.from_path(ip_state_doc_path)
        else:
            ip_state_xml = IpState.from_parameters()
        ip_state_xml.set_doc_path(ip_state_doc_path)

        task_context = DefaultTaskContext(uuid, path, self.task_name, tl)
        task_context.set_ip_state_xml(ip_state_xml)
        task_context.set_premis_manipulate(None) # TODO: set premis manipulate

        return task_context

    def finalize(self, task_context):
        """
        Finalize logging task. Can be called several times to get an updated result object.
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """

        add_result_params={}
        if task_context.ip_state_xml.get_state() < 0:
            task_context.task_logger.adderr("Task status is undefined (-1). Task status must be set in task implementation.")

        if task_context.task_logger.path is not None and not task_context.task_logger.task_logfile.closed:
            task_context.task_logger.task_logfile.close()

        # persist IP state (error, success)
        task_context.ip_state_xml.set_last_task(self.task_name)
        task_context.ip_state_xml.set_state(task_context.task_status)
        task_context.ip_state_xml.write_doc(task_context.ip_state_xml.get_doc_path())

        # set progress
        self.update_state(state='PROGRESS', meta={'process_percent': 100})
        # task result object returned as AsyncResult(task_id).result in celery
        task_result = TaskResult(task_context)

        # add event to PREMIS and write file
        # self.package_premis.add_event('identifier_value', task_context.task_status, 'linking_agent', 'linking_object')
        # if os.path.isfile(os.path.join(task_context.path, 'metadata/PREMIS.xml')):
        #     with open(os.path.join(task_context.path, 'metadata/PREMIS.xml'), 'w') as output_file:
        #         output_file.write(self.package_premis.to_string())

        #end_time = time.time()
        return task_result

    def run_task(self, task_context):
        """
        This method is overriden by the task method implementation (thi one has type 0 in order to not be shown)
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:0,type:0,stage:0
        """
        task_context.task_logger.addinfo("Executing default task (to be overridden)")
        task_context.task_status = 0
        return

    def run(self, uuid, path, additional_input, *args, **kwargs):
        """
        Run method of celery task. This method will be executed by celery.
        This method calls the 'run_task' method which is overridden by the concrete task implementation.

        @type       uuid: str
        @param      uuid: Internal identifier

        @type       path: str
        @param      path: Path where the IP is stored

        @type       path: additional_params
        @param      path: Additional parameters dictionary (passed throuh from actual task implementation to celery result)

        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log, additional parameters)
        """


        # initialize task
        task_context = self.initialize(uuid, path)
        task_context.additional_input = additional_input
        try:
            # check IP state and execute actual task implementation; can return additional result parameters
            # in the dictionary additional_params. This dictionary is stored as part of the celery result
            # and is stored in the result backend (AsyncResult(task_id).result.add_res_parms).
            if task_context.valid(self.accept_input_from, self.task_name):
                task_context.additional_output = self.run_task(task_context)
        except Exception, e:
            task_context.task_logger.adderr("An error occurred: %s" % e)
            traceback.print_exc()
            task_context.task_status = 1
            #self.add_PREMIS_event(self.task_name, 'FAILURE', 'identifier', 'agent', package_premis_file, tl, path)

        return self.finalize(task_context)

    def can_connect(self, task):
        return task in self.accept_input_from

    # def add_PREMIS_event(self, task, outcome, identifier_value,  linking_agent, package_premis_file,
    #                      tl, ip_work_dir):
    #     '''
    #     Add an event to the PREMIS file and update it afterwards.
    #     '''
    #     package_premis_file.add_event(task, outcome, identifier_value, linking_agent)
    #     path_premis = os.path.join(ip_work_dir, "metadata/PREMIS.xml")
    #     with open(path_premis, 'w') as output_file:
    #         output_file.write(package_premis_file.to_string())
    #     tl.addinfo('PREMIS file updated: %s (%s)' % (path_premis, outcome))