# coding=UTF-8
'''
Created on June 9, 2015

@author: Jan Rörden
'''

import os

from config.config import root_dir

import unittest
import glob, os
import subprocess
from fido.fido import Fido

class FormatIdentification():
    """
    File Format Identification
    """
    def __init__(self):
        self.fid = Fido()
        self.fid.handle_matches = self.print_matches
        self.lastFmt = None

    def identify_file(self, entry):
        """
        This function identifies the file format of every file that is handed over.
        """
        self.fid.identify_file(entry)
        return self.lastFmt

    def print_matches(self, fullname, matches, delta_t, matchtype=''):
        #print "####" + fullname
        for (f, s) in matches:
            self.lastFmt = self.fid.get_puid(f)


class TestFormatIdentification(unittest.TestCase):
    def testFido(self):
       delivery_dir = root_dir + '/earkresources/Delivery-test'
       #delivery_dir = root_dir
       vsip = FormatIdentification()

       for subdir, dirs, files in os.walk(delivery_dir):
            for file in files:
                #print subdir
                if subdir != "schemas":
                    fmt = vsip.identify_file(os.path.join(subdir, file))
                    print fmt

       # self.assertTrue(actual)

if __name__ == '__main__':
    unittest.main()
