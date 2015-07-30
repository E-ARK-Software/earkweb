# coding=UTF-8
'''
Created on June 9, 2015

@author: Jan Rörden
'''

import os

from config.config import root_dir

import unittest

class FormatIdentification():
    """
    File Format Identification
    """
    # TODO: Dependency to PREMIS! The JHOVE output must go into the PREMIS file.
    # TODO: Element premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension/premis:mdSecType/premis:mdWrap/premis:xmlData/jhove:jhove

    def _identify_file(self, object):
        """
        This function identifies the file format of every file that is handed over.
        """


    def find_files(self, delivery_dir):
        """
        This function iterates the SIP and selects files where the format should be identified.
        """
        for object in os.listdir(delivery_dir):
            # TODO: "stoplist" of directories: schemas, aip-metadata...?
            # better: recieve correct folder name (=unpacked submission) from unpacking stage
            # this is rather a workaround!
            if object != "schemas":
                if os.path.isdir(os.getcwd()+'/'+delivery_dir+'/'+object+'/content/data'):
                    os.chdir(os.getcwd()+'/'+delivery_dir+'/'+object+'/content/data')
                    for object in os.listdir(os.getcwd()):
                        self._identify_file(object)



class TestFormatIdentification(unittest.TestCase):

    def testValidateXML(self):
        delivery_dir = root_dir + '/workers/resources/Delivery-test/'
        vsip = FormatIdentification()
        actual = vsip.find_files(delivery_dir)
        #self.assertTrue(actual)


if __name__ == '__main__':
    unittest.main()