from earkcore.process.processresult import ProcessResult
from workflow.default_task_context import DefaultTaskContext

class TaskResult(object):
    uuid = ""
    log = []
    err = []
    task_status = 0
    additional_output = None

    def __init__(self, uuid, task_status, log, err, additional_output):
        self.uuid = uuid
        self.task_status = task_status
        self.additional_output = additional_output
        self.log = log
        self.err = err
        #super(TaskResult, self).__init__(success, log, err)

    def __init__(self, task_context):
        self.uuid = task_context.uuid
        self.task_status = task_context.task_status
        self.additional_output = task_context.additional_output
        self.log = task_context.task_logger.log
        self.err = task_context.task_logger.err

if __name__ == "__main__":
    tr = TaskResult(True, ['a', 'b'], ['c','d'], 100, "xyz")
    print tr.state_code

    pr = ProcessResult(True, ['a', 'b'], ['c','d'])
    print pr.success