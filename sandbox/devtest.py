from workers.default_task import DefaultTask
from sandbox.sipgenerator.sipgenerator import SIPGenerator

import os, sys

class SIPExtraction(DefaultTask):

    expected_status = "status==200 or status==390"
    task_status = 300
    error_status = 390

    def run_task(self, uuid, path, tl, additional_params):
        """
        SIP Validation run task method overrides the DefaultTask's run_task method.
        @type       tc: task configuration line (used to insert read task properties in database table)
        @param      tc: order:3,type:1,expected_status:status==200~or~status==390,success_status:300,error_status:390
        """
        os.chdir(path)
        print "Working in rootdir %s" % os.getcwd()
        sipgen = SIPGenerator()
        sipgen.createMets()

