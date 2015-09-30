from earkcore.process.processresult import ProcessResult

class TaskResult(ProcessResult):
    uuid = ""
    state_code = 0
    add_res_parms = None
    def __init__(self, uuid, state_code, success, log, err, additional_result_params):
        self.uuid = uuid
        self.state_code = state_code
        self.add_res_parms = additional_result_params
        super(TaskResult, self).__init__(success, log, err)

if __name__ == "__main__":
    tr = TaskResult(True, ['a', 'b'], ['c','d'], 100, "xyz")
    print tr.state_code

    pr = ProcessResult(True, ['a', 'b'], ['c','d'])
    print pr.success