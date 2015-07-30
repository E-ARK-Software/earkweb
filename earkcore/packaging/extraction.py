import os
import unittest
import tarfile
import shutil

from earkcore.utils import randomutils

from config.config import root_dir

class Extraction(object):
    """
    Extract SIP
    """
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
            tar_object = tarfile.open(name=package_file_path, mode='r')
            tar_object.extractall(path=extract_to)
            return True
        except (ValueError, OSError, IOError, tarfile.TarError),why:
            self._logger.error('Problem to extract %s, why: %s' % (package_file_path,str(why)))
            return False


class TestExtraction(unittest.TestCase):

    delivery_dir = root_dir + '/earkresources/Delivery-test/'
    temp_extract_dir = root_dir + '/tmp/temp-' + randomutils.randomword(10)

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TestExtraction.temp_extract_dir):
            os.makedirs(TestExtraction.temp_extract_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TestExtraction.temp_extract_dir)

    def test_extract_sip(self):
        package_file = self.delivery_dir + 'SIP-sqldump.tar.gz'
        contained_sip_dir = './SIP-1f594d58-d09f-46dd-abac-8432068a7f6d/'
        sip_extraction = Extraction()
        actual = sip_extraction.extract(package_file, TestExtraction.temp_extract_dir)
        self.assertTrue(actual)
        files_to_check = (
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./METS.xml'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./schemas/premis-v2-2.xsd'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./metadata/PREMIS.xml'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./schemas/IP.xsd'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./schemas/xlink.xsd'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./schemas/ExtensionMETS.xsd'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./schemas/jhove.xsd'),
            os.path.join(TestExtraction.temp_extract_dir,contained_sip_dir,'./content/data/census.sql'),
        )
        for file in files_to_check:
            self.assertTrue(os.path.isfile(file), "File %s not found in extracted directory" + file)

if __name__ == '__main__':
    unittest.main()