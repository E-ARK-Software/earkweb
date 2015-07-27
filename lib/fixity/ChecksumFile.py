# coding=UTF-8
'''
Created on June 15, 2015
'''
__author__ = 'shsdev'

from config import log
import lxml
from lxml.etree import XMLSyntaxError
import unittest
import config.params
from ChecksumAlgorithm import ChecksumAlgorithm
import hashlib


class ChecksumFile(object):
    """
    Checksum validation
    """

    blocksize = 65536

    def __init__(self, fpath):
        """
        Constructor takes file path as argument; checksums of different types can then be calculated for this file.

        @type       file: fpath
        @param      file: Path to file
        """
        self.file_path = fpath

    def get(self, checksum_algorithm):
        """
        This function takes the object 'file', calculates the checksum according to the algorithm defined in checksum_algorithm and
        compares it to checksum_expected, which contains the checksum stored in the meta data file.

        @type       checksum_algorithm:  ChecksumAlgorithm
        @param      checksum_algorithm: Algorithm used to create the checksum (taken from METS file)
        @rtype:     string
        @return:    checksum
        """
        hash = None
        if checksum_algorithm == ChecksumAlgorithm.SHA256:
            hash = hashlib.sha256()
        elif checksum_algorithm == ChecksumAlgorithm.MD5:
            hash = hashlib.md5()

        with open(self.file_path, 'rb') as file:
            for block in iter(lambda: file.read(self.blocksize), ''):
                hash.update(block)
        return hash.hexdigest()

class TestChecksum(unittest.TestCase):

    test_dir = config.params.root_dir + '/test/resources/lib/fixity/'
    test_file = test_dir + 'test.txt'
    csobj = ChecksumFile(test_file)

    def test_get_MD5(self):
        """
         Checksum (type MD5) must return SHA256 checksum value
        """
        actual = self.csobj.get(ChecksumAlgorithm.MD5)
        print actual
        self.assertTrue(actual is not None, "Checksum (type MD5) must not be empty")
        self.assertEquals(actual, "098f6bcd4621d373cade4e832627b4f6")

    def test_get_SHA256(self):
        """
        Checksum (type SHA256) must return SHA256 checksum value
        """
        actual = self.csobj.get(ChecksumAlgorithm.SHA256)
        print actual
        self.assertTrue(actual is not None, "Checksum (type SHA256) must not be empty")
        self.assertEquals(actual, "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08")


if __name__ == '__main__':
    unittest.main()