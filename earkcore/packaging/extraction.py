import os, sys
import unittest
import tarfile
import shutil

from earkcore.utils import randomutils

from config.config import root_dir

from earkcore.process.processor import Processor

def default_reporter(percent):
    print "\r{percent:3.0f}%".format(percent=percent)

class Extraction(Processor):
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
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')
            self.log.append("Extracting package %s to %s" % (package_file_path, extract_to))
            tar_object = tarfile.open(name=package_file_path, mode='r', encoding='utf-8')
            members = tar_object.getmembers()
            total = len(members)
            print "Total: " + str(total)
            i = 100; perc = 0
            for member in members:
                if i % 100 == 0:
                    perc = (i*100)/total
                    print "100 processed (item %d) ... (%d)" % (i,perc)
                tar_object.extract(member, extract_to)
                i += 1
            self.success = True
        except (ValueError, OSError, IOError, tarfile.TarError),why:
            self.err.append('Problem to extract %s, why: %s' % (package_file_path,str(why)))
            self.success = False
        return self.result()

    def extract_with_report(self, package_file_path, extract_to, progress_reporter=default_reporter, total=0, current=0):
        try:
            self.log.append("Extracting package %s to %s" % (package_file_path, extract_to))
            import sys
            reload(sys)
            sys.setdefaultencoding('utf8')
            tar_object = tarfile.open(name=package_file_path, mode='r', encoding='utf-8')
            members = tar_object.getmembers()
            total = len(members)
            perc = 0
            for member in members:
                if current % 2 == 0:
                    perc = (current * 100) / total
                    progress_reporter(perc)
                tar_object.extract(member, extract_to)
                current += 1
            self.success = True
        except (ValueError, OSError, IOError, tarfile.TarError),why:
            self.err.append('Problem to extract %s, why: %s' % (package_file_path,str(why)))
            self.success = False
        return self.result()


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
        result = sip_extraction.extract(package_file, TestExtraction.temp_extract_dir)
        self.assertTrue(result.success)
        print result.log[0]
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

    def test_extract_sip_with_report(self):
        package_file = self.delivery_dir + 'SIP-sqldump.tar.gz'
        contained_sip_dir = './SIP-1f594d58-d09f-46dd-abac-8432068a7f6d/'
        sip_extraction = Extraction()
        result = sip_extraction.extract_with_report(package_file, TestExtraction.temp_extract_dir)
        self.assertTrue(result.success)
        print result.log[0]
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
