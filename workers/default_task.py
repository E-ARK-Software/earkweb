from celery import Task
import time, os
from config.config import root_dir
from celery import current_task
from taskresult import TaskResult
import tarfile
from workers.statusvalidation import StatusValidation
from earkcore.metadata.premis.PremisManipulate import Premis
from workflow.ip_state import IpState
import glob
from tasklogger import TaskLogger

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
        # TODO: dependency to root directory must be removed! PREMIS_skeleton not necessary
        premis_skeleton_file = root_dir + '/earkresources/PREMIS_skeleton.xml'
        with open(premis_skeleton_file, 'r') as premis_file:
            package_premis_file = Premis(premis_file)
        package_premis_file.add_agent('eark-aip-creation')
    tl = TaskLogger(task_log_file)
    tl.addinfo(("%s task %s" % (task_name, current_task.request.id)))
    return tl, start_time, package_premis_file


def add_PREMIS_event(task, outcome, identifier_value,  linking_agent, package_premis_file,
                     tl, ip_work_dir):
    '''
    Add an event to the PREMIS file and update it afterwards.
    '''
    package_premis_file.add_event(task, outcome, identifier_value, linking_agent)
    path_premis = os.path.join(ip_work_dir, "metadata/PREMIS.xml")
    with open(path_premis, 'w') as output_file:
        output_file.write(package_premis_file.to_string())
    tl.addinfo('PREMIS file updated: %s' % path_premis)


class DefaultTask(Task, StatusValidation):

    expected_status = "status!=-9999"
    success_status = 0
    error_status = 0

    task_name = "DefaultTask"

    add_result_params = {}

    def run_task(self, uuid, path, tl, additional_params):
        """
        This method is overriden by the task method implementation
        @type tl: list[str]
        @param tl: Task log
        @return: Additional result parameters dictionary
        """
        tl.addinfo("Executing default task (to be overridden)")
        return {}

    def run(self, uuid, path, additional_params, *args, **kwargs):
        """
        Default task
        @type       uuid: str
        @param      uuid: Internal identifier
        @type       path: str
        @param      path: Path where the IP is stored
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log, additional parameters)
        """
        # task name is name of instantiating class
        self.task_name = str(self.__name__)
        # initialize task
        tl, start_time, package_premis_file = init_task2(path, self.task_name, "sip_to_aip_processing")
        self.update_state(state='PROGRESS', meta={'process_percent': 1})
        try:
            # state
            ip_state_doc_path = os.path.join(path, "state.xml")
            ip_state = IpState.from_parameters(self.error_status, False)
            if os.path.exists(ip_state_doc_path):
                ip_state = IpState.from_path(ip_state_doc_path)

            # check state
            tl.err = self.valid_state(ip_state.get_state(), self.expected_status)
            if len(tl.err) > 0:
                return tl.finalize(uuid, self.error_status)

            self.add_result_params = self.run_task(uuid, path, tl, additional_params)

            if len(tl.err) > 0:
                return tl.finalize(uuid, self.error_status)

            # finalize task
            ip_state.set_state(self.success_status)
            # TODO: make sure this gets written in case of error
            ip_state.write_doc(ip_state_doc_path)
            self.update_state(state='PROGRESS', meta={'process_percent': 100})
            add_PREMIS_event('SIPDeliveryValidation', 'SUCCESS', 'identifier', 'agent', package_premis_file, tl, path)
            return tl.finalize(uuid, self.success_status, self.add_result_params)
        except Exception:
            add_PREMIS_event('SIPDeliveryValidation', 'FAILURE', 'identifier', 'agent', package_premis_file, tl, path)
            return tl.finalize(uuid, self.error_status)