class ProcessResult(object):
    def __init__(self, success, log, err):
        """
        Constructor
        @type       success: Boolean
        @param      success: Path to file
        @type       log: List[String]
        @param      log: Processing log
        @type       err: List[String]
        @param      err: Error log
        """
        self.success = success
        self.log = log
        self.err = err
    success = False
    log = []
    err = []
    state = 0
