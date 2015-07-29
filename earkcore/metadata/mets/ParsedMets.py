# coding=UTF-8
'''
Created on June 15, 2015
'''
__author__ = 'shsdev'

from config import log
import lxml
import unittest
import config.params
import hashlib
import os
import lxml
from lxml.etree import XMLSyntaxError


class ParsedMets(object):
    """
    Parsed METS object
    """
    ns = {'mets': 'http://www.loc.gov/METS/', 'xlink': 'http://www.w3.org/1999/xlink',
          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

    _logger = log.init('sip-to-aip-converter')

    mets_tree = None

    def __init__(self, rdir):
        """
        Constructor takes root directory as argument; paths in METS file are relative to this directory.

        @type       rdir: string
        @param      rdir: Path to root directory
        """
        self.root_dir = rdir
        self.mets_tree = None

    def set_parsed_mets(self, pmets):
        """
        Set mets ElementTree object which is parsed already

        @type       pmets: ElementTree
        @param      pmets: Parsed METS
        """
        self.mets_tree = pmets

    def load_mets(self, mets_file_path):
        """
        Load mets Element tree object

        @type       pmets: ElementTree
        @param      pmets: Parsed METS
        """
        self.mets_tree = lxml.etree.parse(mets_file_path)

    def get_root(self):
        if self.mets_tree is None:
            raise ValueError("Attribute 'mets_tree' of type ElementTree must be initialized")
        return self.mets_tree.getroot()

    def get_file_elements(self):
        return self.mets_tree.getroot().xpath('/mets:mets/mets:fileSec/mets:fileGrp/mets:file', namespaces=ParsedMets.ns)

    def get_first_file_element(self):
        file_elements = self.get_file_elements()
        if len(file_elements) > 0:
            return file_elements[0]
        else:
            return None

    @staticmethod
    def get_file_element_checksum(file_element):
        return ''.join(file_element.xpath('@CHECKSUM'))

    @staticmethod
    def get_file_element_checksum_algorithm(file_element):
        return ''.join(file_element.xpath('@CHECKSUMTYPE'))

    def get_mets_schema_from_schema_location(self):
        if self.mets_tree is None:
            raise ValueError("Attribute 'mets_tree' of type ElementTree must be initialized")
        root = self.mets_tree.getroot()
        schema_file = ''
        locations = root.xpath('/mets:mets/@xsi:schemaLocation', namespaces=ParsedMets.ns)
        locations = ''.join(locations)
        locations = locations.split(' ')
        for token in locations:
            if token == ('http://www.loc.gov/METS/'):
                position = locations.index(token)
                schema_location = locations[position + 1]
                if schema_location.startswith('http://'):
                    schema_file = schema_file
                    self._logger.info('New schema location: "%s"' % schema_location)
                elif schema_location.startswith(''):
                    schema_file = self.root_dir + schema_location
                    self._logger.info('New schema location: "%s"' % (self.root_dir + schema_location))
        return schema_file


class TestParsedMets(unittest.TestCase):

    test_dir = config.params.root_dir + '/earkcore/metadata/mets/resources/'
    test_file = test_dir + 'METS_filesec.xml'
    pmets = ParsedMets(test_dir)
    pmets.load_mets(test_file)

    def test_validate_files_size(self):
        """
        Must not validate if the files listed in the METS file does not match the actual file size
        """
        actual = self.pmets.mets_tree.getroot().tag
        self.assertEquals(actual, "{http://www.loc.gov/METS/}mets", "Root tag 'mets' not found")

    def test_get_file_elements(self):
        """
        File elements list must have one file element
        """
        file_elements = self.pmets.get_file_elements()
        self.assertIsNotNone(file_elements, "File elements must not be None")
        self.assertEquals(len(file_elements), 1, "File elements list must have one file element")

    def test_get_first_file_element(self):
        """
        Must return first file element
        """
        file_element = self.pmets.get_first_file_element()
        self.assertEquals(file_element.tag, "{http://www.loc.gov/METS/}file", "Must return a file element")


if __name__ == '__main__':
    unittest.main()
