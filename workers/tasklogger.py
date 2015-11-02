import os
from earkcore.utils.datetimeutils import ts_date
import unittest
from config.config import root_dir
from earkcore.utils import randomutils
from taskresult import TaskResult
from earkcore.metadata.premis import PremisUpdate

class TaskLogger(object):
    """
    Task logger class to organise the handling of log messages in a task. It allows to decide
    if a message is only written to a file or if it is shown on the gui level. The 'fin' method
    closes the file and returns a TaskResult object.
    """

    log = None
    err = None
    path = None
    task_logfile = None

    def __init__(self, path):
        """
        Constructor used to initialise task logger object
        @type       path: string
        @param      path: Path to task log file
        """
        self.path = path
        self.log = []
        self.err = []
        self.open()

    def addinfo(self, message, display=True):
        """
        Add info log message
        @type       message: string
        @param      message: task log message
        @type       display: boolean
        @param      display: true if the message should be transferred to the client (default: True)
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        self.addmsg(message, False, display)

    def adderr(self, message, display=True):
        """
        Add error message
        @type       message: string
        @param      message: task log message
        @type       display: boolean
        @param      display: true if the message should be transferred to the client (default: True)
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        self.addmsg(message, True, display)

    def addmsg(self, message, error, display):
        """
        Add log message
        @type       message: string
        @param      message: task log message
        @type       error: boolean
        @param      error: true if the message is an error message
        @type       display: boolean
        @param      display: true if the message should be transferred to the client (default: True)
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """
        msglist = self.err if error else self.log
        msg_prefix = "ERROR" if error else "INFO"
        # only append message to the list if it should be shown in the gui
        if display:
            msglist.append(message)
        # only write to file if it is open
        if not self.path is None and not self.task_logfile.closed:
            self.task_logfile.write("%s %s %s\n" % (ts_date(), msg_prefix, message))

    def close_logger(self, uuid, ip_state, task_info, add_result_params={}):
        """
        Finalize logging task. Can be called several times to get an updated result object.
        @rtype:     TaskResult
        @return:    Task result (success/failure, processing log, error log)
        """

        # retrieve TaskResult object
        # tr = TaskResult(task_context)

        # Add task result to PREMIS file
        # TODO: retrieve success/failure status from TaskResult
        PremisUpdate.add_event(task_info)

        if self.path is not None and not self.task_logfile.closed:
            self.task_logfile.close()


    def open(self):
        """
        Open task log file at self.path in append mode
        @return:    None
        """
        if self.path is not None and (self.task_logfile is None or self.task_logfile.closed):
            self.task_logfile = open(self.path, 'a+')

class TestTaskLogger(unittest.TestCase):

    temp_log_file = root_dir + '/tmp/temp-' + randomutils.randomword(10)

    @classmethod
    def tearDownClass(cls):
        os.remove(TestTaskLogger.temp_log_file)

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(root_dir + '/tmp/'):
            os.makedirs(root_dir + '/tmp/')

    def test_log(self):
        print self.temp_log_file
        tl = TaskLogger(self.temp_log_file)
        self.assertFalse(tl.task_logfile.closed, "File is closed after initialising")
        tl.addmsg("some message", False, True)
        self.assertEquals(len(tl.log), 1)
        self.assertEquals(len(tl.err), 0)
        self.assertEquals("some message", tl.log[0])

        tl.addmsg("another message", False, True)
        self.assertEquals(len(tl.log), 2)
        self.assertEquals(len(tl.err), 0)
        result = tl.close_logger()
        self.assertTrue(result.success, "Error log is empty, so success must be true")
        self.assertTrue(tl.task_logfile.closed, "File is not closed after finalizing")

        tl.open()
        tl.addmsg("an error occurred", True, True)
        self.assertEquals(len(tl.log), 2)
        self.assertEquals(len(tl.err), 1)
        result = tl.close_logger()
        self.assertFalse(result.success, "Error log is not empty, so success must be false")


if __name__ == '__main__':
    unittest.main()