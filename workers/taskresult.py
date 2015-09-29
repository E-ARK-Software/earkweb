from earkcore.process.processresult import ProcessResult

class TaskResult(ProcessResult):
    uuid = ""
    ip_state = 0
    add_res_parms = None
    def __init__(self, uuid, ip_state, success, log, err, additional_result_params):
        self.uuid = uuid
        self.ip_state = ip_state
        self.add_res_parms = additional_result_params
        super(TaskResult, self).__init__(success, log, err)

if __name__ == "__main__":
    tr = TaskResult(True, ['a', 'b'], ['c','d'], 100, "xyz")
    print tr.ip_state

    pr = ProcessResult(True, ['a', 'b'], ['c','d'])
    print pr.success