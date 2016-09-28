# coding=UTF-8
"""
Created on June 30, 2016
"""
from earkcore.utils.pathutils import package_sub_path_from_relative_path

__author__ = 'shsdev'

import os
import unittest
import lxml
from lxml.etree import XMLSyntaxError
from config.configuration import root_dir


class ParsedEad(object):
    """
    Parsed EAD object
    """
    ead_tree = None
    ead_file_path = None

    def __init__(self, rdir, ead_file_path):
        """
        Constructor takes root directory as argument; paths in EAD file are relative to this directory.

        @type       rdir: string
        @param      rdir: Path to root directory (relative links in the EAD are evaluated according to this path)
        @type       ead_file_path: string
        @param      ead_file_path: Path to the EAD metadata file
        """
        self.ns = {'ead': 'http://ead3.archivists.org/schema/', 'xlink': 'http://www.w3.org/1999/xlink', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

        self.root_dir = rdir
        self.ead_tree = None
        self.ead_file_path = ead_file_path
        self._load_ead(ead_file_path)

    def _load_ead(self, ead_file_path):
        """
        Load ead Element tree object

        @type       ead_file_path: ElementTree
        @param      ead_file_path: Parsed EAD
        """
        if not os.path.exists(ead_file_path):
            raise ValueError('The XML file is not available at the given location: %s' % ead_file_path)
        self.ead_tree = lxml.etree.parse(ead_file_path)

    def get_root(self):
        if self.ead_tree is None:
            raise ValueError("Attribute 'ead_tree' of type ElementTree must be initialized")
        return self.ead_tree.getroot()

    def get_dao_elements(self):
        return self.ead_tree.getroot().xpath('//ead:dao', namespaces=self.ns)

    def _first_md_val_ancpath(self, current_elm, md_tag, text_val_sub_path=None):
        parent_elms = current_elm.findall("..")
        if parent_elms is not None and len(parent_elms) == 1:
            parent = parent_elms[0]
            for child in parent:
                if child.tag == md_tag:
                    if not text_val_sub_path:
                        return child.text
                    else:
                        text_child_elms = child.findall(text_val_sub_path, namespaces=self.ns)
                        if len(text_child_elms) == 1:
                            return text_child_elms[0].text
                        else:
                            return None
                else:
                    for c in child:
                        if c.tag == md_tag:
                            if not text_val_sub_path:
                                return c.text
                            else:
                                text_c_elms = c.findall(text_val_sub_path, namespaces=self.ns)
                                if len(text_c_elms) == 1:
                                    return text_c_elms[0].text
                                else:
                                    return None
            if parent.tag == md_tag:
                return parent.tag
            else:
                return self._first_md_val_ancpath(parent, md_tag, text_val_sub_path)
        else:
            return None

    def dao_path_mdval_tuples(self, md_tag, text_val_sub_path=None):
        md_tag = '{%s}%s' % (self.ns['ead'], md_tag)
        dao_elements = self.get_dao_elements()
        return [{
            "path": package_sub_path_from_relative_path(self.root_dir, self.ead_file_path, dao_elm.attrib['href']),
            "mdvalue": self._first_md_val_ancpath(dao_elm, md_tag, text_val_sub_path)
        } for dao_elm in dao_elements]


class TestParsedEad(unittest.TestCase):
    test_dir = root_dir + '/earkresources/EAD-test/'

    def test_get_root_element(self):
        """
        Must not validate if the files listed in the EAD file does not match the actual file size
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml')
        actual = pead.ead_tree.getroot().tag
        self.assertEquals(actual, "{http://ead3.archivists.org/schema/}ead", "Root tag 'ead' not found")

    def test_get_dao_elements(self):
        """
        Test get dao elements
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml')
        dao_elements = pead.get_dao_elements()
        self.assertIsNotNone(dao_elements, "DAO elements must not be None")
        self.assertEquals(len(dao_elements), 2, "DAO elements list must have two DAO element")

    def test_first_metadata_value_in_ancestry_path(self):
        """
        Test get closest unittitle element value (c04)
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml')
        dao_elements = pead.get_dao_elements()
        for dao_elm in dao_elements:
            self.assertEqual("Record - Adams-Ayers", pead._first_md_val_ancpath(dao_elm, "{http://ead3.archivists.org/schema/}unittitle"))

    def test_first_metadata_value_in_ancestry_path_unitdatestructured(self):
        """
        Test get closest unittitle element value (c04)
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml')
        dao_elements = pead.get_dao_elements()
        for dao_elm in dao_elements:
            self.assertEqual("22.04.2016", pead._first_md_val_ancpath(dao_elm, "{http://ead3.archivists.org/schema/}unitdatestructured", "ead:datesingle"))

    def test_first_metadata_value_in_ancestry_path_c03(self):
        """
        Test get closest unittitle element value (c03)
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example2.xml')
        dao_elements = pead.get_dao_elements()
        for dao_elm in dao_elements:
            self.assertEqual("Adams-Ayers", pead._first_md_val_ancpath(dao_elm, "{http://ead3.archivists.org/schema/}unittitle"))

    def test_first_metadata_value_in_ancestry_path_c02(self):
        """
        Test get closest unittitle element value (c02)
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example3.xml')
        dao_elements = pead.get_dao_elements()
        for dao_elm in dao_elements:
            self.assertEqual("Incoming Correspondence", pead._first_md_val_ancpath(dao_elm, "{http://ead3.archivists.org/schema/}unittitle"))

    def test_first_metadata_value_in_ancestry_path_c01(self):
        """
        Test get closest unittitle element value (c01)
        """
        pead = ParsedEad(TestParsedEad.test_dir, TestParsedEad.test_dir + 'metadata/descriptive/EAD-example4.xml')
        dao_elements = pead.get_dao_elements()
        for dao_elm in dao_elements:
            self.assertEqual("Correspondence", pead._first_md_val_ancpath(dao_elm, "{http://ead3.archivists.org/schema/}unittitle"))

    def test_dao_title_tuples(self):
        """
        Test dao tuples
        """
        root_dir = TestParsedEad.test_dir
        ead_file_path = TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml'
        pead = ParsedEad(root_dir, ead_file_path)
        md_tag = "unittitle"
        res = pead.dao_path_mdval_tuples(md_tag)
        self.assertEqual("representations/rep1/data/Example1.docx", res[0]['path'])
        self.assertEqual("representations/rep2/data/Example1.pdf", res[1]['path'])
        self.assertEqual("Record - Adams-Ayers", res[0]['mdvalue'])
        self.assertEqual("Record - Adams-Ayers", res[1]['mdvalue'])

    def test_dao_unitdatestructured_datevalue_subelement(self):
        """
        Test dao tuples
        """
        root_dir = TestParsedEad.test_dir
        ead_file_path = TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml'
        pead = ParsedEad(root_dir, ead_file_path)
        md_tag = "unitdatestructured"
        res = pead.dao_path_mdval_tuples(md_tag, "ead:datesingle")
        self.assertEqual("22.04.2016", res[0]['mdvalue'])


    def test_dao_clevel_attribute_value(self):
        """
        Test dao tuples
        """
        root_dir = TestParsedEad.test_dir
        ead_file_path = TestParsedEad.test_dir + 'metadata/descriptive/EAD-example1.xml'
        pead = ParsedEad(root_dir, ead_file_path)
        md_tag = "c04"
        res = pead.dao_path_mdval_tuples(md_tag, "@ead:level")
        self.assertEqual("{http://ead3.archivists.org/schema/}c04", res[0]['mdvalue'])


if __name__ == '__main__':
    unittest.main()
