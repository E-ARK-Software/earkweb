class ValidationResult(object):
    def __init__(self, valid, log, err):
        """
        Constructor
        @type       valid: Boolean
        @param      valid: Path to file
        @type       log: List[String]
        @param      log: Processing log
        @type       err: List[String]
        @param      err: Error log
        """
        self.valid = valid
        self.log = log
        self.err = err
    valid = False
    log = []
    err = []