# coding=UTF-8
'''
Created on June 15, 2015
'''

__author__ = 'shsdev'

import unittest
import os
import lxml

from config.config import mets_schema_file
from config.config import premis_schema_file
from lxml import etree
from earkcore.fixity.ChecksumValidation import ChecksumValidation
from earkcore.metadata.XmlHelper import q
from earkcore.utils.fileutils import remove_protocol

XLINK_NS = "http://www.w3.org/1999/xlink"
METS_NS = 'http://www.loc.gov/METS/'


class MetsValidation(object):
    '''
    Validation of the Mets file. This includes also the validation of Premis files that are linked in the amdSec!
    '''

    def __init__(self, root):
        self.validation_errors = []
        self.total_files = 0
        self.schema_mets = etree.XMLSchema(file=mets_schema_file)
        self.schema_premis = etree.XMLSchema(file=premis_schema_file)
        self.rootpath = root
        self.subsequent_mets = []

    def validate_mets(self, mets):
        '''
        Validates a Mets file. The Mets file is parsed with etree.iterparse(), which allows event-driven parsing of
        large files. On certain events/conditions actions are taken, like file validation or adding Mets files found
        inside representations to a list so that they will be evaluated later on.

        @param mets:    Path leading to a Mets file that will be evaluated.
        @return:        Boolean validation result.
        '''
        # TODO: remove processed elements from tree
        if mets.startswith('file://./'):
            mets = os.path.join(self.rootpath, mets[9:])
            # change self.rootpath so it fits any relative path found in the current (subsequent) mets
            self.rootpath = mets.rsplit('/', 1)[0]
        else:
            self.rootpath = mets.rsplit('/', 1)[0]

        try:
            parsed_mets = etree.iterparse(open(mets), events=('start', 'end'), schema=self.schema_mets)
            for event, element in parsed_mets:
                # Define what to do with specific tags.
                if event == 'end' and element.tag == q(METS_NS, 'file'):
                    # files
                    self.total_files += 1
                    self.validate_file(element)
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]
                elif event == 'end' and element.tag == q(METS_NS, 'div') and element.attrib['LABEL'] == 'representations':
                    # representation mets files
                    for element in element.getchildren():
                        rep = element.attrib['LABEL']
                        for child in element:
                            if child.tag == q(METS_NS, 'mptr'):
                                metspath = child.attrib[q(XLINK_NS, 'href')]
                                sub_mets = rep, metspath
                                self.subsequent_mets.append(sub_mets)
                        element.clear()
                        while element.getprevious() is not None:
                            del element.getparent()[0]
                elif event == 'end' and element.tag == q(METS_NS, 'dmdSec'):
                    # dmdSec
                    pass
                elif event == 'end' and element.tag == q(METS_NS, 'amdSec'):
                    # pass
                    if len(element.getchildren()) > 0:
                        for element in element.getchildren():
                            # element = didiprovMD
                            if len(element.getchildren()) > 0:
                                for element in element.getchildren():
                                    # element = mdRef
                                    if element.attrib['MDTYPE'] == 'PREMIS':
                                        if element.attrib[q(XLINK_NS, 'href')].startswith('file://./'):
                                            rel_path = element.attrib[q(XLINK_NS, 'href')]
                                            premis = os.path.join(self.rootpath, rel_path[9:])
                                            try:
                                                parsed_premis = etree.iterparse(open(premis), events=('start',), schema=self.schema_premis)
                                                for event, element in parsed_premis:
                                                    pass
                                                print 'Successfully validated Premis file: %s' % premis
                                            except etree.XMLSyntaxError, e:
                                                print 'VALIDATION ERROR: The Premis file %s yielded errors:' % premis
                                                print e.error_log
                                                self.validation_errors.append(e.error_log)
                                        else:
                                            pass
                                    else:
                                        pass
        except etree.XMLSyntaxError, e:
            self.validation_errors.append(e.error_log)

        if self.total_files != 0:
            self.validation_errors.append('File count yielded %d instead of 0.' % self.total_files)

        # enable/disable error logging to console
        print 'Error log for METS file: ', mets
        for error in self.validation_errors:
            print error

        return True if len(self.validation_errors) == 0 else False


    def validate_file(self, file):
        '''
        Validates every file found inside a Mets, so far: size, checksum, fixity. If a file exists, the counter for
        self.total_files is diminished.

        @param file:    XML Element of a file that will be validated.
        @return:
        '''
        err = []
        log = []

        # get information about the file
        attr_path =  file.getchildren()[0].attrib[q(XLINK_NS,'href')]
        attr_size = file.attrib['SIZE']
        attr_checksum = file.attrib['CHECKSUM']
        attr_checksumtype = file.attrib['CHECKSUMTYPE']
        # mimetpye = file.attrib['MIMETYPE']

        # check if file exists, if yes validate it
        fitem = remove_protocol(attr_path)
        file_path = os.path.join(self.rootpath, fitem).replace('\\', '/')
        if not os.path.exists(file_path):
            err.append("Unable to find file referenced in delivery METS file: %s" % file_path)
        else:
            self.total_files -= 1
            # check if file size is valid
            # TODO: is this even needed?
            file_size = os.path.getsize(file_path)
            if not int(file_size) == int(attr_size):
                err.append("Actual file size %s does not equal file size attribute value %s" % (file_size, attr_size))
                # workaround for earkweb.log in AIP metadata/ folder on IP root level
                if file_path[-22:] == './metadata/earkweb.log':
                    err.pop()
                    log.append('Forced validation result \'True\' for file: %s' % (file_path))

            # validate checksum
            checksum_validation = ChecksumValidation()
            checksum_result = checksum_validation.validate_checksum(file_path, attr_checksum, attr_checksumtype)

            # workaround for earkweb.log in AIP metadata/ folder on IP root level
            if file_path[-22:] == './metadata/earkweb.log':
                checksum_result = True

            if not checksum_result == True:
                err.append('Checksum validation failed for: %s' % file_path)

        for error in err:
            print 'File validation error: ' + error
            self.validation_errors.append(error)



class TestMetsValidation(unittest.TestCase):
    # TODO: add one test each for a valid and a faulty Mets
    rootpath = '/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/'

    def test_IP_mets(self):
        mets_validator = MetsValidation(self.rootpath)
        mets_validator.validate_mets(os.path.join(self.rootpath, 'METS.xml'))
        for rep, metspath in mets_validator.subsequent_mets:
            # print 'METS file for representation: %s at path: %s' % (rep, metspath)
            subsequent_mets_validator = MetsValidation(self.rootpath)
            subsequent_mets_validator.validate_mets(os.path.join(metspath))


if __name__ == '__main__':
    unittest.main()