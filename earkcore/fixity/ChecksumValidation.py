# coding=UTF-8
'''
Created on June 15, 2015
'''
__author__ = 'shs'

import unittest
from ChecksumAlgorithm import ChecksumAlgorithm
from ChecksumFile import ChecksumFile
from config.config import root_dir

class ChecksumValidation(object):
    """
    Checksum validation
    """

    def validate_checksum(self, file_path, checksum_expected, checksum_algorithm):
        """
        This function takes the object 'file', calculates the checksum according to the algorithm defined in checksum_algorithm and
        compares it to checksum_expected, which contains the checksum stored in the meta data file.

        @type       file_path: string
        @param      file: Path to file
        @type       checksum_expected:  string
        @param      checksum_expected:  Expected checksum (taken from METS file)
        @type       checksum_algorithm:  ChecksumAlgorithm
        @param      checksum_algorithm: Algorithm used to create the checksum (taken from METS file)
        @rtype:     bool
        @return:    Validity of checksum
        """
        checksum_file = ChecksumFile(file_path)
        calculated_checksum = checksum_file.get(checksum_algorithm)
        return (calculated_checksum == checksum_expected)

class TestChecksumValidation(unittest.TestCase):

    test_directory = root_dir + '/earkcore/fixity/resources/'
    test_file = test_directory + 'test.txt'

    csval = ChecksumValidation()

    def test_validate_valid_MD5(self):
        """
        Must validate a correct MD5 checksum
        """
        expected = ""
        actual = self.csval.validate_checksum(self.test_file, "098f6bcd4621d373cade4e832627b4f6", ChecksumAlgorithm.MD5)
        self.assertTrue(actual, "Must validate a correct MD5 checksum")

    def test_notvalidate_invalid_MD5(self):
        """
        Must validate a correct MD5 checksum
        """
        expected = ""
        actual = self.csval.validate_checksum(self.test_file, "incorrect_md5", ChecksumAlgorithm.MD5)
        self.assertFalse(actual, "Must not validate an incorrect MD5 checksum")

    def test_validate_valid_SHA256(self):
        """
        Must validate a correct SHA256 checksum
        """
        expected = ""
        actual = self.csval.validate_checksum(self.test_file, "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", ChecksumAlgorithm.SHA256)
        self.assertTrue(actual, "Must validate a correct SHA256 checksum")

    def test_notvalidate_invalid_SHA256(self):
        """
        Must validate a correct SHA256 checksum
        """
        expected = ""
        actual = self.csval.validate_checksum(self.test_file, "incorrect_sha256", ChecksumAlgorithm.SHA256)
        self.assertFalse(actual, "Must not validate an incorrect SHA256 checksum")

if __name__ == '__main__':
    unittest.main()