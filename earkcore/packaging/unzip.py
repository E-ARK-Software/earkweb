""" unzip.py

    Extract a zipfile.

"""

import sys

sys.path.append("/opt/python_wsgi_apps/earkweb")

import zipfile
import os
import os.path
import unittest
import shutil
from earkcore.process.processor import Processor

from earkcore.utils import randomutils

from config.configuration import root_dir

def default_reporter(percent):
    print "\rProgress: {percent:3.0f}%".format(percent=percent)

class Unzip(Processor):

    def extract_with_report(self, file, dir, progress_reporter=default_reporter):
        self.percent = 10
        try:
            if not dir.endswith(':') and not os.path.exists(dir):
                os.mkdir(dir)

            zf = zipfile.ZipFile(file)

            # create directory structure
            self._createstructure(file, dir)

            num_files = len(zf.namelist())

            self.log.append("Extracting %s items (directories and files)" % num_files)

            percent = self.percent
            divisions = 100 / percent

            perc = int(num_files / divisions)

            # extract files to directory structure
            for i, name in enumerate(zf.namelist()):
                if perc > 0 and (i % perc) == 0 and i > 0:
                    complete = int (i / perc) * percent
                    progress_reporter(complete)

                if not name.endswith('/'):
                    outfile = open(os.path.join(dir, name), 'wb')
                    outfile.write(zf.read(name))
                    outfile.flush()
                    outfile.close()
            num_f = sum([len(files) for r, d, files in os.walk(dir)])
            self.log.append("Extracted %s files" % num_f)
            self.success = True
        except (ValueError, OSError, IOError),why:
            self.err.append('Problem to extract %s, why: %s' % (file,str(why)))
            self.success = False
        return self.result()

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    @classmethod
    def _makedirs(self, directories, basedir):
        """ Create directories """
        for dir in directories:
            curdir = os.path.join(basedir, dir)
            if not os.path.exists(curdir):
                os.makedirs(curdir)

    @classmethod
    def _listdirs(self, file):
        """ Get the directories """
        zf = zipfile.ZipFile(file)
        dirs = []
        filelist = filter( lambda x: not x.endswith( '/' ), zf.namelist() )
        for f in filelist:
            path, filename = os.path.split(f)
            if path.startswith("/"):
                path = path[1:len(path)]
            dirs.append(path)
        dirs.sort()
        return dirs

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
        print "Extracting to %s" % self.temp_extract_dir
        package_file = self.delivery_dir + 'SIP-sqldump.zip'
        contained_sip_dir = './SIP-1f594d58-d09f-46dd-abac-8432068a7f6d/'
        sip_extraction = Unzip()
        result = sip_extraction.extract_with_report(package_file, TestExtraction.temp_extract_dir)
        self.assertTrue(result.success)
        for log in result.log:
            print log
        # must be 8 extracted files
        cpt = sum([len(files) for r, d, files in os.walk(TestExtraction.temp_extract_dir)])
        self.assertEqual(cpt, 8, "Number of extracted files not as expected")
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

