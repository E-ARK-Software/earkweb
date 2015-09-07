class StatusValidation(object):

    def valid_state(self, ip, tc):
        err = []
        # logical expression in variable 'expected_status' uses 'status' as the variable for the current information package status
        status = ip.statusprocess
        expected_status = tc.expected_status
        if not eval(tc.expected_status):
            _append_err_msg(err, status, expected_status)
        return err

def check_status(status, expected_status, err):
    status = status
    if not eval(expected_status):
        _append_err_msg(err, status, expected_status)

def _append_err_msg(err, status, expected_status):
    err.append("Incorrect information package status (value 'status=%d' evaluated against the locical expression '%s')" % (status, expected_status))