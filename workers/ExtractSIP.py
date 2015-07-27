import os
import unittest
import tarfile
import shutil

import lxml
from lxml.etree import tostring

from config import log
import utils.randomutils

import config.params

class SIPExtraction(object):
    """
    Extract SIP
    """

    _logger = log.init('sip-to-aip-converter')

    def extract(self,package_file_path, extract_to):
        """
        This function extracts a SIP file to a target directory.

        @type       package_file_path: string
        @param      package_file_path: Path to file
        @type       extract_to:  string
        @param      extract_to:  Expected checksum (taken from METS file)
        @rtype:     bool
        @return:    success of extraction
        """
        try:
            sip_tar_object = tarfile.open(name=package_file_path, mode='r')
            sip_tar_object.extractall(path=extract_to)
            return True
        except (ValueError, OSError, IOError, tarfile.TarError),why:
            self._logger.error('Problem to extract %s, why: %s' % (package_file_path,str(why)))
            return False


class TestXMLValidation(unittest.TestCase):

    delivery_dir = config.params.root_dir + '/test/resources/Delivery-test/'
    temp_extract_dir = config.params.root_dir + '/test/temp-' + utils.randomutils.randomword(10)

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TestXMLValidation.temp_extract_dir):
            os.makedirs(TestXMLValidation.temp_extract_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TestXMLValidation.temp_extract_dir)

    def test_extract_sip(self):
        package_file = self.delivery_dir + 'SIP-sqldump.tar.gz'
        contained_sip_dir = './SIP-1f594d58-d09f-46dd-abac-8432068a7f6d/'
        sip_extraction = SIPExtraction()
        actual = sip_extraction.extract(package_file, TestXMLValidation.temp_extract_dir)
        self.assertTrue(actual)
        files_to_check = (
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./METS.xml'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./schemas/premis-v2-2.xsd'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./metadata/PREMIS.xml'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./schemas/IP.xsd'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./schemas/xlink.xsd'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./schemas/ExtensionMETS.xsd'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./schemas/jhove.xsd'),
            os.path.join(TestXMLValidation.temp_extract_dir,contained_sip_dir,'./content/data/census.sql'),
        )
        for file in files_to_check:
            self.assertTrue(os.path.isfile(file), "File %s not found in extracted directory" + file)

if __name__ == '__main__':
    unittest.main()