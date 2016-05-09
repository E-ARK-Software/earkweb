from __future__ import generators
from earkcore.packaging.unzip import Unzip
from earkcore.packaging.untar import Untar
import os
import os.path
import unittest
import shutil

from earkcore.utils import randomutils

from config.configuration import root_dir

from earkcore.packaging.packageformat import PackageFormat

"""
Base extraction class.

Extract implementation class must implement method:
extract_with_report(package_file, target_folder, progress_reporter=custom_reporter)
"""
class Extract(object):
    def factory(filename):
        if PackageFormat.get(filename) == PackageFormat.TAR: return Untar()
        if PackageFormat.get(filename) == PackageFormat.ZIP: return Unzip()
        assert 0, "Package format not supported"
    factory = staticmethod(factory)

class TestExtract(unittest.TestCase):

    delivery_dir = root_dir + '/earkresources/Delivery-test/'
    temp_extract_dir = root_dir + '/tmp/temp-' + randomutils.randomword(10)

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TestExtract.temp_extract_dir):
            os.makedirs(TestExtract.temp_extract_dir)

    @classmethod
    def tearDownClass(cls):
        pass

    def reset_test_dir(self):
        shutil.rmtree(TestExtract.temp_extract_dir)
        os.makedirs(TestExtract.temp_extract_dir)

    def test_extract_sip_zip(self):
        package_file = self.delivery_dir + 'SIP-sqldump.zip'
        self.extr(package_file)
        self.reset_test_dir()

    def test_extract_sip_tar(self):
        package_file = self.delivery_dir + 'SIP-sqldump.tar'
        self.extr(package_file)
        self.reset_test_dir()

    def extr(self, package_file):
        contained_sip_dir = './SIP-1f594d58-d09f-46dd-abac-8432068a7f6d/'

        _, file_extension = os.path.splitext(package_file)
        sip_extraction = Extract.factory(file_extension)
        #sip_extraction = Unzip()

        result = sip_extraction.extract_with_report(package_file, TestExtract.temp_extract_dir)
        self.assertTrue(result.success)
        for log in result.log:
            print log
        # must be 8 extracted files
        cpt = sum([len(files) for r, d, files in os.walk(TestExtract.temp_extract_dir)])
        self.assertEqual(cpt, 8, "Number of extracted files not as expected")
        files_to_check = (
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./METS.xml'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./schemas/premis-v2-2.xsd'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./metadata/PREMIS.xml'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./schemas/IP.xsd'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./schemas/xlink.xsd'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./schemas/ExtensionMETS.xsd'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./schemas/jhove.xsd'),
            os.path.join(TestExtract.temp_extract_dir,contained_sip_dir,'./content/data/census.sql'),
        )
        for file in files_to_check:
            self.assertTrue(os.path.isfile(file), "File %s not found in extracted directory" + file)

if __name__ == '__main__':
    unittest.main()

