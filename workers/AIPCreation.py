# coding=UTF-8
'''
Created on Mar 2, 2015

@author: Jan Rörden
'''
import shutil

import sys
import os
import io
import StringIO
from shutil import copytree
import utils.randomutils
import unittest
import config.params

from config import log

from lib.metadata.mets.AIPMetsCreation import AIPMetsCreation


class AIPCreation(object):
    _logger = log.init('sip-to-aip-converter')    

    def __init__(self, working_directory):
        self.working_directory = working_directory
        self._logger.info("Working directory: %s" % working_directory)
        # if not os.path.exists(working_directory):
        #     os.makedirs(working_directory)


    def create_AIP_skeleton(self, working_directory):
        """
        Create AIP skeleton
        """
        for folder in config.params.aip_folders:
            os.mkdir(os.path.join(working_directory, folder))        
        

    def copy_submission(self, extracted_sip_directory):
        """
        Copy extracted SIP to working area

        @type       extracted_sip_directory: string
        @param      extracted_sip_directory: Path to extracted SIP directory
        @rtype:     bool
        @return:    Success of AIP preparation
        """
        #for file in os.listdir(extracted_sip_directory):
        #    print 'Copy file %s to working area.' % file
        
        submission_directory = os.path.join(self.working_directory, 'submission')
        
        copytree(extracted_sip_directory, submission_directory)

        
    def create_AIP_METS(self, working_directory):
        """
        Create the AIP METS file
        """
        mets_creator = AIPMetsCreation()
        mets_creation = mets_creator.create_METS(working_directory)



class TestAIPCreation(unittest.TestCase):

    extracted_sip_dir = config.params.root_dir + '/test/resources/Delivery-test/SIP-sqldump'
    temp_working_dir = config.params.root_dir + '/test/temp-aip-dir-' + utils.randomutils.randomword(10)

    aip_creation = AIPCreation(temp_working_dir)

    @classmethod
    def tearDownClass(cls):
        #shutil.rmtree(TestAIPCreation.temp_working_dir)
        return

    def test_copy_submission(self):
        self.aip_creation.copy_submission(self.extracted_sip_dir)
        files_to_check = (
            os.path.join(TestAIPCreation.temp_working_dir,'submission/METS.xml'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/schemas/premis-v2-2.xsd'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/metadata/PREMIS.xml'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/schemas/IP.xsd'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/schemas/xlink.xsd'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/schemas/ExtensionMETS.xsd'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/schemas/jhove.xsd'),
            os.path.join(TestAIPCreation.temp_working_dir,'submission/content/data/census.sql'),
        )
        for file in files_to_check:
            self.assertTrue(os.path.isfile(file), "File %s not found in submission directory" % file)


    def test_create_AIP_structure(self):
        self.aip_creation.create_AIP_skeleton(self.temp_working_dir)
        
        for folder in config.params.aip_folders:
            self.assertTrue(os.path.isdir(os.path.join(TestAIPCreation.temp_working_dir, folder)), "Folder %s not found in AIP directory" % folder)
    
            
    def test_create_METS_AIP(self):
        self.aip_creation.create_AIP_METS(self.temp_working_dir)
        self.assertTrue(os.path.isfile(os.path.join(TestAIPCreation.temp_working_dir, 'METS.xml')), "METS not found on root level")
    
    

if __name__ == '__main__':
    unittest.main()
