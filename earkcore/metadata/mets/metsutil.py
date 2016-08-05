#!/usr/bin/env python
# coding=UTF-8
__author__ = "Sven Schlarb"
__copyright__ = "Copyright 2016, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"
import glob
from earkcore.metadata.mets.ParsedMets import ParsedMets
import os
import unittest
from config.configuration import root_dir


def get_package_mets_files_from_basedir(base_directory):
        """
        Get list of information package METS file paths based on a directory which contains information packages in subdirectories.

        @type       base_directory: str
        @param      base_directory: Directory which contains information packages in subdirectories.
        @rtype:     list
        @return:    String list of information package METS file paths
        """
        glob_expr = '%s/*/METS.xml' % base_directory
        mets_files = glob.glob(glob_expr)
        return mets_files


def get_mets_obj_id(mets_file_path):
        """
        Get identifier from mets file

        @type       mets_file_path: str
        @param      mets_file_path: METS file path
        @rtype:     str
        @return:    Object identifier
        """
        package_path, file_name = os.path.split(mets_file_path)
        pm = ParsedMets(package_path)
        pm.load_mets(mets_file_path)
        return str(pm.get_obj_id())


def get_mets_objids_from_basedir(base_directory):
        """
        Get list of OBJID strings from METS files based on a directory which contains information packages in subdirectories.

        @type       base_directory: str
        @param      base_directory: Directory which contains information packages in subdirectories.
        @rtype:     list
        @return:    Object identifier
        """
        mets_file_paths = get_package_mets_files_from_basedir(base_directory)
        mets_obj_ids = []
        for mets_file_path in mets_file_paths:
            mets_obj_ids.append(get_mets_obj_id(mets_file_path))
        return mets_obj_ids


class METSUtilTest(unittest.TestCase):

    def test_get_package_mets_files_in_directory(self):
        """
        Must return METS.xml files of information package directories contained in a given directory
        """
        mets_files = get_package_mets_files_from_basedir(os.path.join(root_dir, 'earkresources/AIP-test'))
        self.assertTrue(len(mets_files) > 0)
        for mets_file in mets_files:
            self.assertTrue(mets_file.endswith("METS.xml"))

    def test_get_identifier_from_mets(self):
        """
        Must return METS.xml files of information package directories contained in a given directory
        """
        mets_file = os.path.join(root_dir, 'earkresources/AIP-test/siardpackage/METS.xml')
        self.assertEqual("urn:uuid:89b8ab18-79f5-4893-bb22-0b25399901b5", get_mets_obj_id(mets_file))

    def test_get_mets_objids_from_basedir(self):
        objids = get_mets_objids_from_basedir(os.path.join(root_dir, 'earkresources/AIP-test'))
        self.assertTrue(len(objids) > 0)


if __name__ == '__main__':
    unittest.main()
