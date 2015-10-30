# coding=UTF-8
'''
Created on Mar 2, 2015

@author: Jan Rörden (based on: http://alex-sansom.info/content/validating-xml-against-xml-schema-python)
@author: Sven Schlarb
'''

import hashlib
import unittest

import lxml
from lxml.etree import XMLSyntaxError

from earkcore.xml.xmlvalidation import XmlValidation
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm
from earkcore.fixity.ChecksumValidation import ChecksumValidation
from earkcore.metadata.mets.MetsValidation import MetsValidation
from earkcore.metadata.mets.ParsedMets import ParsedMets
from config.config import root_dir
from earkcore.xml.validationresult import ValidationResult

class DeliveryValidation(object):
    """
    SIP delivery validation
    """
    # Clear any previous errors
    lxml.etree.clear_error_log()
    def getFileElements(self, deliveryDir, delivery_xml_file, schema_file):
        log = []
        log.append("Validating delivery: %s using schema: %s" % (delivery_xml_file, schema_file))
        try:
            # Parse the XML file, get the root element
            parsed_mets = ParsedMets(deliveryDir)
            parsed_mets.load_mets(delivery_xml_file)
            # If the XSD file wasn't found, extract location from the XML
            if schema_file == None:
                schema_file = parsed_mets.get_mets_schema_from_schema_location()
            # Parse the XSD file
            parsed_sfile = lxml.etree.parse(schema_file)
            # Validate the delivery XML file
            xmlVal = XmlValidation()
            validation_result = xmlVal.validate_XML(parsed_mets.mets_tree, parsed_sfile)
            if validation_result:
                return parsed_mets.get_file_elements()
        except (XMLSyntaxError), why:
            errmsg = 'Error validating delivery %s, why: %s' % (delivery_xml_file, str(why))
        return None


    def validate_delivery(self, deliveryDir, delivery_xml_file, schema_file, package_file):
        """
        Validate the delivery METS document. Does XML validation of the delivery METS file and fixity check on file
        level.

        @type       deliveryDir: string
        @param      deliveryDir: Path to delivery directory
        @type       delivery_xml_file:  string
        @param      delivery_xml_file:  Path to delivery METS file.
        @type       package_file:  string
        @param      package_file:  Path to package file file (e.g. TAR).
        @rtype:     ValidationResult
        @return:    Validation result (validity, process log, error log)
        """
        valid = False
        log = []
        err = []
        valid_xml = False
        valid_checksum = False
        log.append("Validating delivery: %s using schema: %s and package file %s" % (
            delivery_xml_file, schema_file, package_file))

        try:
            # Parse the XML file, get the root element
            parsed_mets = ParsedMets(deliveryDir)
            parsed_mets.load_mets(delivery_xml_file)
            # If the XSD file wasn't found, extract location from the XML
            if schema_file == None:
                schema_file = parsed_mets.get_mets_schema_from_schema_location()
            # Parse the XSD file
            parsed_sfile = lxml.etree.parse(schema_file)
            # Validate the delivery XML file
            xmlVal = XmlValidation()
            validation_result = xmlVal.validate_XML(parsed_mets.mets_tree, parsed_sfile)
            valid_xml = validation_result
            # Checksum validation
            checksum_expected = ParsedMets.get_file_element_checksum(parsed_mets.get_first_file_element())
            checksum_algorithm = ParsedMets.get_file_element_checksum_algorithm(parsed_mets.get_first_file_element())
            csval = ChecksumValidation()
            valid_checksum = csval.validate_checksum(package_file, checksum_expected, ChecksumAlgorithm.get(checksum_algorithm))
            # Mets validation
            mval = MetsValidation(parsed_mets)
            valid_files_size = mval.validate_files_size()

            log += validation_result.log
            err += validation_result.err

            log += valid_files_size.log
            err += valid_files_size.err

            log.append("Checksum validity: \"%s\"" % str(valid_checksum))

            valid = (valid_xml.valid and valid_checksum and valid_files_size.valid)

            return ValidationResult(valid, log, err)

        except (XMLSyntaxError), why:
            errmsg = 'Error validating delivery %s, why: %s' % (delivery_xml_file, str(why))
            err.append(errmsg)
            return ValidationResult(False, log, err)

        return ValidationResult(valid, log, err)


class TestSIPDeliveryValidation(unittest.TestCase):

    delivery_dir = root_dir + '/earkresources/Delivery-test/'

    schema_file = delivery_dir + 'schemas/IP.xsd'
    package_file = delivery_dir + 'SIP-sqldump.tar.gz'
    vsip = DeliveryValidation()

    def test_validate_delivery(self):
        """
        Delivery must be valid if all validation tests succeed
        """
        delivery_file = self.delivery_dir + 'Delivery.SIP-sqldump.xml'
        actual = self.vsip.validate_delivery(self.delivery_dir, delivery_file, self.schema_file, self.package_file)
        self.assertTrue(actual, "Delivery must be valid if all validation tests succeed")


if __name__ == '__main__':
    unittest.main()
