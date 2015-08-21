# coding=UTF-8
'''
Created on June 15, 2015
'''
__author__ = 'shsdev'

import unittest
import os

from ParsedMets import ParsedMets
from config.config import root_dir
from earkcore.xml.validationresult import ValidationResult

class MetsValidation(object):
    """
    METS validation
    """
    ns = {'mets': 'http://www.loc.gov/METS/', 'xlink': 'http://www.w3.org/1999/xlink',
          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    parsed_mets = None

    def __init__(self, pmets):
        """
        Constructor takes parsed mets object as argument

        @type       parsed_mets: ParsedMets
        @param      parsed_mets: Parsed mets object
        """
        self.parsed_mets = pmets

    def validate_files_size(self):
        """
        Compare file size values of mets: file elements to the actual file size of the referenced files.
        File paths in the METS fileSec are relative to the root directory initialized by the constructor.
        It is required to initialize the parsed_mets attribute before validating the fileSec of the METS.

        @rtype:     bool
        @return:    Validity of size values
        """
        valid = True
        log = []
        err = []
        if self.parsed_mets is None:
            err.append("Attribute 'parsed_mets' of type ElementTree must be initialized")

        mets_file_elms = self.parsed_mets.mets_tree.getroot().xpath('//mets:file', namespaces=MetsValidation.ns)
        if (len(mets_file_elms) == 0):
            err.append("No mets:file elements found")
            return False
        for mets_file_elm in mets_file_elms:
            fileloc = mets_file_elm.xpath('mets:FLocat/@xlink:href', namespaces=MetsValidation.ns)
            if (len(fileloc) != 1):
                err.append("Unable to determine file location reference in METS file")
                valid = False
            package_file_path = os.path.join(self.parsed_mets.root_dir, fileloc[0])
            if not os.path.isfile(package_file_path):
                err.append("Unable to find referenced file in delivery METS file")
                valid = False
            size_elms = mets_file_elm.xpath('@SIZE', namespaces={'mets': 'http://www.loc.gov/METS/'})
            if not (len(size_elms) == 1 and size_elms[0].isdigit()):
                err.append("SIZE attribute value is not a digit")
                valid = False
            package_file_size = os.path.getsize(package_file_path)
            size_attr_value = int(size_elms[0])
            if not package_file_size == size_attr_value:
                err.append("Actual file size %d does not equal file size attribute value %d" % (
                    package_file_size, size_attr_value))
                valid = False
        log.append("File size validity: \"%s\"" % str(valid))
        return ValidationResult(valid, log, err)

class TestMetsValidation(unittest.TestCase):

    test_dir = root_dir + '/earkcore/metadata/mets/resources/'

    def test_validate_files_size(self):
        """
        Validates if the files listed in the METS file match the actual file size
        """
        test_file = self.test_dir + 'METS_filesec.xml'
        parsed_mets = ParsedMets(self.test_dir)
        parsed_mets.load_mets(test_file)
        mval = MetsValidation(parsed_mets)
        actual = mval.validate_files_size()
        self.assertTrue(actual.valid, "Validates if the files listed in the METS file match the actual file size")

    def test_not_validate_wrong_filesize(self):
        """
        Must not validate if the file size is wrong
        """
        test_file = self.test_dir + 'METS_file_size_wrong.xml'
        parsed_mets = ParsedMets(self.test_dir)
        parsed_mets.load_mets(test_file)
        mval = MetsValidation(parsed_mets)
        actual = mval.validate_files_size()
        self.assertFalse(actual.valid, "Must not validate if the file size is wrong")

if __name__ == '__main__':
    unittest.main()
