import time

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
    #additional_data = None
    #additional_data = None

    additional_data = None

    def __init__(self, uuid, path, task_name, task_logger, additional_data):
        self.uuid = uuid
        self.path = path
        self.task_name = task_name
        self.task_logger = task_logger
        self.start_time = time.time()
        self.additional_data = additional_data

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
        if status != 0 and not "Reset" in current_task_name:
            self.task_logger.adderr("An error occurred ('task status=%d')" % status)

        last_task = self.ip_state_xml.get_last_task()
        if not "Reset" in current_task_name and last_task != 'All' and last_task not in accept_input_from:
            self.task_logger.adderr(
                "Task cannot be executed at the current task state (last executed task: %s, input accepted from previous tasks: %s)" % (last_task, str(accept_input_from)))
        return len(self.task_logger.err) == 0
