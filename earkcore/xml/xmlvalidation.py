#!/usr/bin/env python
# coding=UTF-8
__author__ = "Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

import os
import unittest
from config.config import root_dir
from validationresult import ValidationResult
from earkcore.utils.fileutils import read_file_content
from xmlschemanotfound import XMLSchemaNotFound

import lxml.etree as ET

class XmlValidation(object):
    """
    XML validation class
    """

    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    XS = '{http://www.w3.org/2001/XMLSchema}'

    SCHEMA_TEMPLATE = """<?xml version = "1.0" encoding = "UTF-8"?>
    <schema xmlns="http://www.w3.org/2001/XMLSchema">
    </schema>"""

    def get_schema_from_instance(self, xml):
        print xml
        xml_dir, tail = os.path.split(xml)

        xml_content = read_file_content(xml)
        tree = ET.XML(xml_content)
        schema_tree = ET.XML(self.SCHEMA_TEMPLATE)

        #Find instances of xsi:schemaLocation
        schema_locations = set(tree.xpath("//*/@xsi:schemaLocation", namespaces={'xsi': self.XSI}))
        for schema_location in schema_locations:
            namespaces_locations = schema_location.strip().split()
            # Import all fnamspace/schema location pairs
            for namespace, location in zip(*[iter(namespaces_locations)] * 2):
                loc = os.path.abspath(os.path.join(xml_dir, location))
                if not os.path.exists(loc):
                    print "ERROR: XML-Schema file not found: %s" % loc
                    raise XMLSchemaNotFound("XML-Schema file not found: %s" % loc)
                xs_import = ET.Element(self.XS + "import")
                xs_import.attrib['namespace'] = namespace
                xs_import.attrib['schemaLocation'] = loc
                schema_tree.append(xs_import)
        return schema_tree

    def validate_XML_by_path(self, xml_path, schema_path):
        """
        This function validates the XML meta data file (parsed_mfile) describing the SIP against the .xsd (sfile),
        which is either contained in the SIP or referenced in the .xml

        @type       xml_path: string
        @param      xml_path: Path to XML file
        @type       schema_path:  string
        @param      schema_path:  Path to schema file.
        @rtype:     ValidationResult
        @return:    Validation result (valid: true/false, processing log, error log)
        """
        validationResult = ValidationResult(False, [], [])
        if schema_path is None:
            validationResult.log.append("XML validation using schemata defined by the schemaLocation attribute.")
        try:
            parsed_schema = ET.parse(schema_path) if schema_path is not None else self.get_schema_from_instance(xml_path)
            parsed_xml = ET.parse(xml_path)
            validationResult = self.validate_XML(parsed_xml, parsed_schema)
        except XMLSchemaNotFound, (instance):
            validationResult.err.append("The XML file contains invalid XML-Schema file references. Please verify 'schemaLocation' attribute.")
            validationResult.err.append(instance.parameter)
        except ET.XMLSchemaParseError, xspe:
            # Something wrong with the schema (getting from URL/parsing)
            validationResult.err.append("XMLSchemaParseError occurred!")
            validationResult.err.append(xspe)
        except ET.XMLSyntaxError, xse:
            # XML not well formed
            validationResult.err.append("XMLSyntaxError occurred!")
            validationResult.err.append(xse)
        finally:
            return validationResult

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
        log = []
        err = []
        try:
            # Validate parsed XML against schema returning a readable message on failure
            schema = ET.XMLSchema(parsed_schema)
            # Validate parsed XML against schema returning boolean value indicating success/failure
            log.append('Schema validity: "%s"' % schema.validate(parsed_xml))
            schema.assertValid(parsed_xml)
            valid_xml = True
        except ET.XMLSchemaParseError, xspe:
            # Something wrong with the schema (getting from URL/parsing)
            err.append("XMLSchemaParseError occurred!")
            err.append(xspe)
        except ET.XMLSyntaxError, xse:
            # XML not well formed
            err.append("XMLSyntaxError occurred!")
            err.append(xse)
        except ET.DocumentInvalid, di:
            # XML failed to validate against schema
            err.append("DocumentInvalid occurred!")
            error = schema.error_log.last_error
            if error:
                # All the error properties (from libxml2) describing what went wrong
                err.append('domain_name: ' + error.domain_name)
                err.append('domain: ' + str(error.domain))
                err.append('filename: ' + error.filename)  # '<string>' cos var is a string of xml
                err.append('level: ' + str(error.level))
                err.append('level_name: ' + error.level_name)  # an integer
                err.append('line: ' + str(error.line))  # a unicode string that identifies the line where the error occurred.
                err.append('message: ' + error.message)  # a unicode string that lists the message.
                err.append('type: ' + str(error.type))  # an integer
                err.append('type_name: ' + error.type_name)
        finally:
            return ValidationResult(valid_xml, log, err)

class TestXmlValidation(unittest.TestCase):

    test_directory = root_dir + '/earkcore/xml/resources/'
    schema_file = test_directory + 'schema.xsd'
    #print schema_file

    xmlval = XmlValidation()

    def test_validate_valid(self):
        """
        Must return valid for a valid XML
        """
        xml_file = self.test_directory + 'instance.xml'
        print xml_file

        actual = self.xmlval.validate_XML_by_path(xml_file, self.schema_file)
        self.assertTrue(actual.valid, "Must return valid for a valid XML")

    def test_validate_notwellformed(self):
        """
        Must return false for a not-well-formed XML
        """
        xml_file = self.test_directory + 'notwellformed_instance.xml'

        actual = self.xmlval.validate_XML_by_path(xml_file, self.schema_file)
        self.assertFalse(actual.valid, "Must return false for a not-well-formed XML")

    def test_validate_notvalid(self):
        """
        Must return false if an element is not defined by the schema
        """
        xml_file = self.test_directory + 'notvalid_instance.xml'

        actual = self.xmlval.validate_XML_by_path(xml_file, self.schema_file)
        self.assertFalse(actual.valid, "Must return false if an element is not defined by the schema")

if __name__ == '__main__':
    unittest.main()