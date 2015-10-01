from celery import Task
import time, os
from config.config import root_dir
from celery import current_task
from taskresult import TaskResult
import tarfile
from workers.statusvalidation import StatusValidation
from earkcore.metadata.premis.PremisManipulate import Premis
from workflow.default_task_context import DefaultTaskContext
from workflow.ip_state import IpState
import glob
from tasklogger import TaskLogger
import traceback


class DefaultTask(Task):

    # Only task specific constants should be defined here, each run method execution has its own task execution context.
    # Gets set by the implementation to indicate accepted output from other tasks
    accept_input_from = []
    # Task name is name of instantiating class (is set by the concrete task implementation)
    task_name = ""

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
        # if os.path.isfile(metadata_dir + '/PREMIS.xml'):
        #     premis_file = open(metadata_dir + '/PREMIS.xml', 'rw')
        #     premis_manipulate = Premis(premis_file)
        # else:
        #     premis_manipulate = Premis()
        #     premis_manipulate.add_agent('eark-aip-creation')

        # get state, try reading current state from state.xml, otherwise set default to is error state,
        # which must then be set to success state explicitely.
        ip_state_doc_path = os.path.join(path, "state.xml")
        if os.path.exists(ip_state_doc_path):
            ip_state_xml = IpState.from_path(ip_state_doc_path)
        else:
            ip_state_xml = IpState.from_parameters()
        ip_state_xml.set_doc_path(ip_state_doc_path)

        # TODO: make nice constructor and eventually set ip_state_xml and premis_manipulate above like task_context.ip_state_xml = and task_context.premis_manipulate =
        task_context = DefaultTaskContext()
        task_context.start_time = time.time()
        task_context.uuid = uuid
        task_context.path = path
        task_context.task_logger = tl
        task_context.premis_manipulate = None #premis_manipulate
        task_context.ip_state_xml = ip_state_xml

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

        #end_time = time.time()
        return task_result

    def run_task(self, task_context):
        """
        This method is overriden by the task method implementation
        @type tl: list[str]
        @param tl: Task log
        @return: Additional result parameters dictionary
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
                self.run_task(task_context)
                print "Variable task_context.task_status after run_task: %s" % task_context.task_status

        except Exception:
            traceback.print_exc()
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