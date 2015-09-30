from earkcore.process.processresult import ProcessResult

class TaskResult(object):
    uuid = ""
    log = []
    err = []
    task_status = 0
    add_res_parms = None

    def __init__(self, uuid, task_status, log, err, additional_result_params):
        self.uuid = uuid
        self.task_status = task_status
        self.add_res_parms = additional_result_params
        self.log = log
        self.err = err
        #super(TaskResult, self).__init__(success, log, err)

if __name__ == "__main__":
    tr = TaskResult(True, ['a', 'b'], ['c','d'], 100, "xyz")
    print tr.state_code

    pr = ProcessResult(True, ['a', 'b'], ['c','d'])
    print pr.success