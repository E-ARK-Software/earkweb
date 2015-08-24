class StatusValidation(object):

    def valid_state(self, ip, tc):
        err = []
        if  tc.expected_status != -1 and ip.statusprocess != tc.expected_status and ip.statusprocess != tc.error_status:
            err.append("Incorrect information package status (must be %d or %d)" % (tc.expected_status, tc.error_status))
        return err