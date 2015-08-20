from earkcore.process.processresult import ProcessResult

class Processor( object ):
    success = False
    log = None
    err = None
    def __init__(self):
        self.log = []
        self.err = []
    def result(self):
        return ProcessResult(self.success, self.log, self.err)