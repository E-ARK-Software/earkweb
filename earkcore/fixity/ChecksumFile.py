# coding=UTF-8
'''
Created on June 15, 2015
'''
__author__ = 'shsdev'

import os
import lxml
from lxml.etree import XMLSyntaxError
import unittest
from ChecksumAlgorithm import ChecksumAlgorithm
import hashlib
from config.config import root_dir
from earkcore.utils.fileutils import remove_protocol

def get_sha256_hash(file):
    blocksize = 65536
    hash = hashlib.sha256()
    print file
    with open(file, 'rb') as file:
        for block in iter(lambda: file.read(blocksize), ''):
            hash.update(block)
    return hash.hexdigest()

def checksum(file_path, wd=None, alg=ChecksumAlgorithm.SHA256):
    fp = remove_protocol(file_path)
    path = fp if wd is None else os.path.join(wd,fp)
    return ChecksumFile(path).get(alg)

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
        This function calculates the checksum using the algorithm specified by the argument 'checksum_algorithm'.
        @type       checksum_algorithm:  ChecksumAlgorithm
        @param      checksum_algorithm: Algorithm used to create the checksum (taken from METS file)
        @rtype:     string
        @return:    checksum
        """
        hash = None
        if checksum_algorithm == ChecksumAlgorithm.SHA256 or checksum_algorithm == 'SHA-256':
            hash = hashlib.sha256()
        elif checksum_algorithm == ChecksumAlgorithm.MD5 or checksum_algorithm == 'MD5':
            hash = hashlib.md5()

        # TODO: change when all tasks reworked for new MetsValidation.py
        #if checksum_algorithm == 'SHA-256':
        #    hash = hashlib.sha256()
        #elif checksum_algorithm == 'MD5':
        #    hash = hashlib.md5()

        with open(self.file_path, 'rb') as file:
            for block in iter(lambda: file.read(self.blocksize), ''):
                hash.update(block)
        return hash.hexdigest()

class TestChecksum(unittest.TestCase):

    test_dir = root_dir + '/earkcore/fixity/resources/'
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