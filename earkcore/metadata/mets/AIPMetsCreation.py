# coding=UTF-8
"""
Created on June 26th, 2015

@author: Jan Rörden
"""
import unittest
import os
import shutil
import datetime
import time

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import SubElement
from config.config import root_dir


class AIPMetsCreation(object):
    """
    Create the AIP METS file
    """
    def __init__(self, package, location):
        self.status = 0
        self.location = location
        self.package = package

        # self.metadatadir = 'dir name'
        # self.contentdir = 'directory name'
        # self.schemadir = 'dir name'

        self.create_METS()

    def descendpackage(self):
        for directory, subdirectories, files in os.walk(self.location + self.package, topdown=True):
            if directory[-8:] == 'Metadata':
                pass
            elif directory[-7:] == 'Schemas':
                pass
            elif directory[-7:] == 'Content':
                self.descendcontent(directory)
            elif directory.rsplit('/', 1)[1] == self.package:
                pass

    def descendcontent(self, contentdir):
        for directory, subdirectories, files in os.walk(contentdir, topdown=True):
            if files.__len__() > 0:
                for filename in files:
                    relativepath =  directory[len(self.location + self.package):]
                    self.write_fileSec(filename, relativepath)

    def create_METS(self):
        # Add to self
        self.uuid = self.package
        self.ns = {'mets': 'http://www.loc.gov/METS/', 
                   'xlink': 'http://www.w3.org/1999/xlink',
                   'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        
        # register namespaces   
        ET.register_namespace('mets', 'http://www.loc.gov/METS/')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        ET.register_namespace('ext', 'ExtensionMETS')
        
        # parse METS template      
        mets_template = ET.parse('/home/jan/Development/earkweb/earkcore/metadata/mets/resources/METS_filesec.xml')
        template_root = mets_template.getroot()
        
        # write info to METS root 
        mets_root = self.write_mets_root(template_root)
        
        # write into METS sections
        template_metsHdr = template_root.find('./mets:metsHdr', namespaces = self.ns)
        metsHdr = self.write_metsHdr(template_metsHdr)
        
        template_amdSec = template_root.find('./mets:amdSec', namespaces = self.ns)
        amdSec = self.write_amdSec(template_amdSec)

        template_fileSec = template_root.find('./mets:fileSec', namespaces = self.ns)
        self.template_fileSec_fileGrp_submissions = SubElement(template_fileSec, 'mets:fileGrp', attrib={'USE': 'submission'})

        self.descendpackage()

        # write METS.xml file into the AIP
        os.chdir('/home/jan/Development/areas/metsresults')
        mets_template.write('METS.xml', xml_declaration = True, encoding = 'UTF-8')
        
    def write_mets_root(self, root):
        """
        Set attributes of <mets> tag.
        """
        objid = self.uuid
        root.set('OBJID', objid)
        # label
        # type
        # id
    
    def write_metsHdr(self, metsHdr):
        """
        Set attributes of <metsHdr> tag and its children.
        
        TODO: every attribute, text etc. should be retrieved from a database.
        """
        timestamp = str(datetime.datetime.now()) # local time
        
        metsHdr.set('CREATEDATE', timestamp)
        metsHdr.set('ext:OAISSTATUS', 'AIC')
        metsHdr.set('RECORDSTATUS', 'NEW')
        
        """
        Defining functions for <metsHdr> children.
        """
        def write_metsHdr_agent(self, attributes, name, note):
            # add a new <agent> child to <metsHdr>
            metsHdr_agent = SubElement(metsHdr, 'mets:agent', attrib=attributes)
            metsHdr_agent_name = SubElement(metsHdr_agent, 'mets:name').text = name
            metsHdr_agent_note = SubElement(metsHdr_agent, 'mets:note').text = note
        
        def write_metsHdr_metsDocumentID(self, text):
            metsHdr_metsDocumentID = SubElement(metsHdr, 'mets:metsDocumentID').text = text
        
        # variables need to come from a database
        attributes = {'ROLE': 'ARCHIVIST', 
                      'TYPE': 'ORGANIZATION'}
        name = 'archivist'
        note = 'some note'
        text = 'METS.xml'
        
        # TODO: add_child: as many calls as needed (dynamic)
        add_child = write_metsHdr_agent(self, attributes, name, note)
        add_child = write_metsHdr_metsDocumentID(self, text)
            
    
    def write_dmdSec(self, dmdSec):
        return 
    
    
    def write_amdSec(self, amdSec):
        # techMD
        # rightsMD
        # digiprovMD
        return
    
    
    def write_fileSec(self, filename, relativepath):
        submission_files = self.template_fileSec_fileGrp_submissions
        attributes = {'ID': 'id',
                      'ADMID': 'admid',
                      'MIMETYPE': 'mime',
                      'SIZE': 'size',
                      'CHECKSUMTYPE': 'check',
                      'CHECKSUM': 'sum',
                      'CREATED': 'date'}
        upath = unicode(relativepath, 'utf-8')
        uname = unicode(filename, 'utf-8')
        new_file = SubElement(submission_files, 'mets:file', attrib=attributes)
        SubElement(new_file, 'mets:FLocat', attrib={'LOCTYPE': 'URL',
                                                    'xlink:href': upath+'/'+uname,
                                                    'xlink:type': 'simple'})

    
    def write_structMap(self, structMap):
        return
    
    
    def control_validity(self, file):
        """
        Check if the created XML file is valid.
        """
        return


def scan(location):
    mets_creation_list = []
    status = 0
    while status == 0:
        aip_list = os.listdir(location)
        # print 'scanning: ' + location
        for package in aip_list:
            if package not in mets_creation_list:
                mets_creation_list.append(package)
                AIPMetsCreation(package, location)
        time.sleep(1)



"""
class TestAIPMetsCreation(unittest.TestCase):
    
    aip_mets_creation = AIPMetsCreation(object)
    
"""

if __name__ == '__main__':
    scan('/home/jan/Development/areas/working/')


    