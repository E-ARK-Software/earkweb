# from earkcore.process.processresult import ProcessResult
#
#
# class TaskResult(object):
#     uuid = ""
#     log = []
#     err = []
#     task_status = 0
#     task_name = ""
#     additional_output = None
#
#     def __init__(self, uuid, task_status, log, err, additional_output):
#         self.uuid = uuid
#         self.task_status = task_status
#         self.additional_output = additional_output
#         self.log = log
#         self.err = err
#         #super(TaskResult, self).__init__(success, log, err)
#
#     def __init__(self, task_context):
#         self.uuid = task_context.uuid
#         self.task_status = task_context.task_status
#         self.additional_output = task_context.additional_output
#         self.log = task_context.task_logger.log
#         self.err = task_context.task_logger.err
#         self.last_task = task_context.task_name
#         self.last_change = task_context.ip_state_xml.get_lastchange()
#
#
# if __name__ == "__main__":
#     tr = TaskResult(True, ['a', 'b'], ['c','d'], 100, "xyz")
#     print tr.state_code
#
#     pr = ProcessResult(True, ['a', 'b'], ['c','d'])
#     print pr.success