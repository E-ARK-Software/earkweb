#!/usr/bin/env python
# coding=UTF-8
__author__ = "Jan Rörden, Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

from config import log
import config.params
import lxml
from lxml.etree import XMLSyntaxError
import unittest

class XmlValidation(object):
    """
    XML validation class
    """

    _logger = log.init('sip-to-aip-converter')

    def validate_XML_by_path(self, xml_path, schema_path):
        """
        This function validates the XML meta data file (parsed_mfile) describing the SIP against the .xsd (sfile),
        which is either contained in the SIP or referenced in the .xml

        @type       xml_path: string
        @param      xml_path: Path to XML file
        @type       schema_path:  string
        @param      schema_path:  Path to schema file.
        @rtype:     bool
        @return:    Validity of XML
        """
        self._logger.debug("Validating XML file %s against schema file %s" % (xml_path,schema_path))
        try:
            parsed_schema = lxml.etree.parse(schema_path)
            parsed_xml = lxml.etree.parse(xml_path)
            return self.validate_XML(parsed_xml, parsed_schema)
        except lxml.etree.XMLSchemaParseError, xspe:
            # Something wrong with the schema (getting from URL/parsing)
            self._logger.error("XMLSchemaParseError occurred!")
            self._logger.error(xspe)
            return False
        except lxml.etree.XMLSyntaxError, xse:
            # XML not well formed
            self._logger.error("XMLSyntaxError occurred!")
            self._logger.error(xse)
            return False

    def validate_XML(self, parsed_xml, parsed_schema):
        """
        This function validates the XML meta data file (parsed_mfile) describing the SIP against the .xsd (sfile),
        which is either contained in the SIP or referenced in the .xml

        @type       parsed_xml: ElementTree
        @param      parsed_xml: METS ElementTree object
        @type       parsed_schema:  ElementTree
        @param      parsed_schema:  Schema file XSD ElementTree object
        @rtype:     bool
        @return:    Validity of XML
        """
        valid_xml = False
        try:
            # Validate parsed XML against schema returning a readable message on failure
            schema = lxml.etree.XMLSchema(parsed_schema)
            # Validate parsed XML against schema returning boolean value indicating success/failure
            self._logger.info('Schema validity: "%s".' % schema.validate(parsed_xml))
            schema.assertValid(parsed_xml)
            valid_xml = True
        except lxml.etree.XMLSchemaParseError, xspe:
            # Something wrong with the schema (getting from URL/parsing)
            self._logger.error("XMLSchemaParseError occurred!")
            self._logger.error(xspe)
            return False
        except lxml.etree.XMLSyntaxError, xse:
            # XML not well formed
            self._logger.error("XMLSyntaxError occurred!")
            self._logger.error(xse)
            return False
        except lxml.etree.DocumentInvalid, di:
            # XML failed to validate against schema
            self._logger.info("DocumentInvalid occurred!")
            error = schema.error_log.last_error
            if error:
                # All the error properties (from libxml2) describing what went wrong
                self._logger.error('domain_name: ' + error.domain_name)
                self._logger.error('domain: ' + str(error.domain))
                self._logger.error('filename: ' + error.filename)  # '<string>' cos var is a string of xml
                self._logger.error('level: ' + str(error.level))
                self._logger.error('level_name: ' + error.level_name)  # an integer
                self._logger.error(
                    'line: ' + str(error.line))  # a unicode string that identifies the line where the error occurred.
                self._logger.error('message: ' + error.message)  # a unicode string that lists the message.
                self._logger.error('type: ' + str(error.type))  # an integer
                self._logger.error('type_name: ' + error.type_name)
            return False
        return valid_xml

class TestXmlValidation(unittest.TestCase):

    test_directory = config.params.root_dir + '/test/resources/lib/xml/'
    schema_file = test_directory + 'schema.xsd'
    print schema_file

    xmlval = XmlValidation()

    def test_validate_valid(self):
        """
        Must return valid for a valid XML
        """
        xml_file = self.test_directory + 'instance.xml'
        print xml_file

        actual = self.xmlval.validate_XML_by_path(xml_file, self.schema_file)
        self.assertTrue(actual, "Must return valid for a valid XML")

    def test_validate_notwellformed(self):
        """
        Must return false for a not-well-formed XML
        """
        xml_file = self.test_directory + 'notwellformed_instance.xml'

        actual = self.xmlval.validate_XML_by_path(xml_file, self.schema_file)
        self.assertFalse(actual, "Must return false for a not-well-formed XML")

    def test_validate_notvalid(self):
        """
        Must return false if an element is not defined by the schema
        """
        xml_file = self.test_directory + 'notvalid_instance.xml'

        actual = self.xmlval.validate_XML_by_path(xml_file, self.schema_file)
        self.assertFalse(actual, "Must return false if an element is not defined by the schema")

if __name__ == '__main__':
    unittest.main()