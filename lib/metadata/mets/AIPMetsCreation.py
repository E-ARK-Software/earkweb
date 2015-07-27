# coding=UTF-8
"""
Created on June 26th, 2015

@author: Jan Rörden
"""
from config import log

import unittest
import os
import shutil
import config.params
import datetime

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import SubElement


class AIPMetsCreation(object):
    """
    Create the AIP METS file
    """
    #def __init__(self, working_directory):
    #    os.chdir(working_directory)
    
    
    def create_METS(self, working_directory):
        # Add to self
        self.uuid = working_directory.rsplit('/', 1)[1]
        self.ns = {'mets': 'http://www.loc.gov/METS/', 
                   'xlink': 'http://www.w3.org/1999/xlink',
                   'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        
        # register namespaces   
        ET.register_namespace('mets', 'http://www.loc.gov/METS/')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        ET.register_namespace('ext', 'ExtensionMETS')
        
        # parse METS template      
        mets_template = ET.parse(config.params.root_dir+'/lib/metadata/mets/template_METS.xml')
        template_root = mets_template.getroot()
        
        # write info to METS root 
        mets_root = self.write_mets_root(template_root)
        
        # write into METS sections
        template_metsHdr = template_root.find('./mets:metsHdr', namespaces = self.ns)
        metsHdr = self.write_metsHdr(template_metsHdr)
        
        template_amdSec = template_root.find('./mets:amdSec', namespaces = self.ns)
        amdSec = self.write_amdSec(template_amdSec)
        
        # write METS.xml file into the AIP
        os.chdir(working_directory)
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
    
    
    def write_fileSec(self, fileSec):
        # submission
        # representation
        # schemas
        return
    
    
    def write_structMap(self, structMap):
        return
    
    
    def control_validity(self, file):
        """
        Check if the created XML file is valid.
        """
        return


"""
class TestAIPMetsCreation(unittest.TestCase):
    
    aip_mets_creation = AIPMetsCreation(object)
    

if __name__ == '__main__':
    unittest.main()

"""
    