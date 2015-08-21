class TaskConfig(object):
    expected_status = 0
    success_status = 0
    error_status = 0
    def __init__(self, exp, sxs, err):
        """
        Constructor
        @type       expected_status: Integer
        @param      expected_status: Expected status
        @type       success_status: Integer
        @param      success_status: Success status
        @type       error_status: Integer
        @param      error_status: Error status
        """
        self.expected_status = exp
        self.success_status = sxs
        self.error_status = err