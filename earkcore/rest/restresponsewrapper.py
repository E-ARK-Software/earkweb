class ResponseWrapper(object):
    """
    ResponseWrapper class
    """

    def __init__(self, success, response=None, status_code=0):
        """
        Constructor of the ResponseWrapper class
        @type       success: string
        @param      success: Valid response received
        @type       response: string
        @param      response: Response object (None if request was not executed)
        @type       status_code: string
        @param      status_code: Response status code
        """
        self.success = success
        if success:
            self.response = response
            self.status_code = self.response.status_code
            self.hdfs_path_id = "none" if self.status_code != 201 else self.response.headers['location'].rpartition('/files/')[2]
        else:
            self.status_code = status_code
            self.hdfs_path_id = "none"
