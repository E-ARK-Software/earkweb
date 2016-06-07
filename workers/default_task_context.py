import time
import unittest
from workers.tasklogger import TaskLogger


class DefaultTaskContext(object):
    uuid = ""
    path = ""
    task_name = ""
    task_status = -1
    task_logger = None
    ip_state_xml = None
    premis_manipulate = None
    start_time = 0
    end_time = 0
    event_type = None
    #additional_data = None
    #additional_data = None

    additional_data = None

    def __init__(self, uuid, path, task_name, task_logger, additional_data, package_premis):
        self.uuid = uuid
        self.path = path
        self.task_name = task_name
        self.task_logger = task_logger
        self.start_time = time.time()
        self.additional_data = additional_data
        self.package_premis = package_premis

    def set_ip_state_xml(self, ip_state_xml):
        self.ip_state_xml = ip_state_xml

    def set_premis_manipulate(self, premis_manipulate):
        self.premis_manipulate = premis_manipulate

    def get_runtime_ms(self):
        if self.end_time > self.start_time:
            return self.end_time - self.start_time
        else:
            return 0

    def valid(self, accept_input_from, current_task_name):
        status = self.ip_state_xml.get_state()
        if (status == 1 or status == -1) and not "Reset" in current_task_name:
            self.task_logger.adderr("Task execution request rejected ('package task_status=%d')" % status)

        last_task = self.ip_state_xml.get_last_task()
        if not "Reset" in current_task_name and last_task != 'All' and last_task not in accept_input_from:
            self.task_logger.adderr(
                "Task cannot be executed at the current task state (last executed task: %s, input accepted from previous tasks: %s)" % (last_task, str(accept_input_from)))
        return len(self.task_logger.err) == 0

    def has_required_parameters(self, check_params):
        return not False in [self.additional_data.has_key(check_param) for check_param in check_params]

    def report_parameter_errors(self, check_params):
        for check_param in check_params:
            if not self.additional_data.has_key(check_param):
                self.task_logger.adderr("Parameter is not defined in task context: %s" % check_param)
        return self.additional_data



class TestSolr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_check(self):
        additional_data = {'identifier': "xyz987", "location": "/tmp/loc"}
        tl = TaskLogger("/tmp/test")
        dftc = DefaultTaskContext("abc123", "/tmp/abc123/", "test_task", tl, additional_data, None)

        check_params = ['identifier', "location"]

        self.assertTrue(dftc.has_required_parameters(check_params))

        check_params += ['does_not_exist']
        self.assertFalse(dftc.has_required_parameters(check_params))

        print dftc.report_parameter_errors(check_params)


if __name__ == '__main__':
    unittest.main()
