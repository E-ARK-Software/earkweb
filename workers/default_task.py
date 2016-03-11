import os
import traceback

from celery import Task
from celery import current_task

from earkcore.metadata.premis.premisgenerator import PremisGenerator
from tasklogger import TaskLogger
from workers.ip_state import IpState


class DefaultTask(Task):

    # Only task specific constants should be defined here, each run method execution has its own task execution context.
    # Gets set by the implementation to indicate accepted output from other tasks
    accept_input_from = []
    # Task name is name of instantiating class (is set by the concrete task implementation)
    task_name = ""

    # premis_manipulate = ""

    def __init__(self):
        self.task_name = str(self.__name__)

    def initialize(self, task_context):
        # create directories if they do not exist
        if not os.path.exists(task_context.path):
            os.mkdir(task_context.path)

        metadata_dir = os.path.join(task_context.path, 'metadata')
        if not os.path.exists(metadata_dir):
            os.mkdir(metadata_dir)

        # task logger
        if not task_context.task_logger:
            task_log_file = os.path.join(metadata_dir, "%s.log" % "earkweb")
            tl = TaskLogger(task_log_file)
            task_context.task_logger = tl
        task_context.task_logger.addinfo(("%s task %s" % (self.task_name, current_task.request.id)))
        task_context.task_logger.addinfo("Processing package %s" % task_context.uuid)

        self.update_state(state='PROGRESS', meta={'process_percent': 1})

        # create PREMIS file or return handle to task
        # premis_manipulate = None
        path_premis = os.path.join(metadata_dir, 'preservation/premis.xml')
        if os.path.isfile(path_premis):
            task_context.package_premis = path_premis
        else:
            premisgen = PremisGenerator(task_context.path)
            premisgen.createPremis()
            task_context.package_premis = path_premis

        # get state, try reading current state from state.xml, otherwise set default to is error state,
        # which must then be set to success state explicitely.
        ip_state_doc_path = os.path.join(task_context.path, "state.xml")
        if os.path.exists(ip_state_doc_path):
            ip_state_xml = IpState.from_path(ip_state_doc_path)
        else:
            ip_state_xml = IpState.from_parameters()
        ip_state_xml.set_doc_path(ip_state_doc_path)

        task_context.task_name = self.task_name

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

        # add event to PREMIS and write file (only if PREMIS file exists)
        package = task_context.uuid
        if os.path.exists(task_context.package_premis):
            outcome = 'success' if task_context.task_status == 0 else 'failure'
            if task_context.additional_data is not None and task_context.additional_data['identifier'] is not None:
                package = task_context.additional_data['identifier']
                # This construction hopefully means that the IdentifierAssignment can be used at any time in the AIP creation process.

            # TODO: clarify relationship between task and event 1->1 or 1->m
            # currently if event_type is set the premis_event gets persisted
            if task_context.event_type:
                eventinfo = {'outcome': outcome,
                             'task_name': self.task_name,
                             'event_type': task_context.event_type,
                             'linked_object': package}
                premisgen = PremisGenerator(task_context.path)
                premisgen.addEvent(task_context.package_premis, eventinfo)

        # set progress
        self.update_state(state='PROGRESS', meta={'process_percent': 100})
        # task result object returned as AsyncResult(task_id).result in celery
        #task_result = TaskResult(task_context)

        #end_time = time.time()
        return task_context

    def run_task(self, task_context):
        """
        This method is overriden by the task method implementation (thi one has type 0 in order to not be shown)
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:0,type:0,stage:0
        """
        task_context.task_logger.addinfo("Executing default task (to be overridden)")
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
        print "Executing %s task." % self.task_name
        task_context = self.initialize(task_context)
        try:
            # check IP state and execute actual task implementation; can return additional result parameters
            # in the dictionary additional_params. This dictionary is stored as part of the celery result
            # and is stored in the result backend (AsyncResult(task_id).result.add_res_parms).
            if task_context.valid(self.accept_input_from, self.task_name):
                task_context.additional_data = self.run_task(task_context) # IMPORTANT: task has to return task_context.additional_data!
        except Exception, e:
            task_context.task_logger.adderr("An error occurred: %s" % e)
            traceback.print_exc()
            task_context.task_status = 1

        return self.finalize(task_context)

    def can_connect(self, task):
        return task in self.accept_input_from
