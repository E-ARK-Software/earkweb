from sqlalchemy.sql.functions import char_length

__author__ = 'bartham'
import os, sys
import time, os
import urlparse
from earkcore.utils.xmlutils import pretty_xml_string
from lxml import etree, objectify
import unittest
import hashlib
import uuid
from mimetypes import MimeTypes
from earkcore.utils.datetimeutils import get_file_ctime_iso_date_str, ts_date, DT_ISO_FORMAT
import urllib

from config.config import root_dir
from datetime import datetime
from subprocess import Popen, PIPE

from earkcore.format.formatidentification import FormatIdentification
from earkcore.utils.fileutils import remove_protocol
from earkcore.metadata.XmlHelper import q, XSI_NS

PREMIS_NS = 'info:lc/xmlns/premis-v2'
PREMIS_NSMAP = {None: PREMIS_NS}
P = objectify.ElementMaker(
    annotate=False,
    namespace=PREMIS_NS,
    nsmap=PREMIS_NSMAP)

METS_NS = 'http://www.loc.gov/METS/'
METSEXT_NS = 'ExtensionMETS'
XLINK_NS = "http://www.w3.org/1999/xlink"
METS_NSMAP = { None: METS_NS, "xlink" : "http://www.w3.org/1999/xlink", "ext" : METSEXT_NS, "xsi" : "http://www.w3.org/2001/XMLSchema-instance" }

M = objectify.ElementMaker(
    annotate=False,
    namespace=METS_NS,
    nsmap=METS_NSMAP)

class SIPGenerator(object):
    fid = FormatIdentification()
    mime = MimeTypes()

    def sha256(self, fname):
        hash = hashlib.sha256()
        with open(fname) as f:
            for chunk in iter(lambda: f.read(4096), ""):
                hash.update(chunk)
        return hash.hexdigest()

    def createAgent(self,role, type, other_type, name, note):
        agent = M.agent({"ROLE":role,"TYPE":type, "OTHERTYPE": other_type}, M.name(name), M.note(note))
        return agent

    def runCommand(self, program, stdin = PIPE, stdout = PIPE, stderr = PIPE):
        result, res_stdout, res_stderr = None, None, None
        try:
            # quote the executable otherwise we run into troubles
            # when the path contains spaces and additional arguments
            # are presented as well.
            # special: invoking bash as login shell here with
            # an unquoted command does not execute /etc/profile

            print 'Launching: '+ ' '.join(program)
            process = Popen( program, stdin = stdin, stdout = stdout, stderr = stderr, shell = False)

            res_stdout, res_stderr = process.communicate()
            result = process.returncode
            print 'Finished: '+ ' '.join(program)

        except Exception as ex:
            res_stderr = ''.join(str(ex.args))
            result = 1

        if result != 0:
            print 'Command failed:' + ''.join(res_stderr)
            raise Exception('Command failed:' + ''.join(res_stderr))

        return result, res_stdout, res_stderr

    def addFiles(self, folder, mets_filegroup):
        ids = []
        for top, dirs, files in os.walk(folder):
            for fn in files:
                file_name = os.path.join(top, fn)
                file_url = unicode(os.path.join("file://",file_name), "utf-8")
                file_mimetype,_ = self.mime.guess_type(file_url)
                file_checksum = self.sha256(file_name)
                file_size = os.path.getsize(file_name)
                #file_cdate = datetime.fromtimestamp(os.path.getctime(file_name)).strftime('%Y-%m-%dT%H:%M:%S%z')
                file_cdate = get_file_ctime_iso_date_str(file_name)
                file_id = "ID"+uuid.uuid1().__str__()
                mets_file = M.file({"MIMETYPE":file_mimetype, "CHECKSUMTYPE":"SHA-256", "CREATED":file_cdate, "CHECKSUM":file_checksum, "USE":"Datafile", "ID":file_id, "SIZE":file_size})
                mets_filegroup.append(mets_file)
                mets_FLocat = M.FLocat({q(XLINK_NS, 'href'): file_url,"LOCTYPE":"URL", q(XLINK_NS, 'type'): 'simple'})
                mets_file.append(mets_FLocat)
                ids.append(file_id)
        return ids

    def createPremis(self, enable_jhove = False):
        jhove_parser = None
        if enable_jhove == True:
            jhove_parser = etree.XMLParser(remove_blank_text=True)

        PREMIS_ATTRIBUTES = {"version" : "2.0"}
        premis = P.premis(PREMIS_ATTRIBUTES)
        premis.attrib['{%s}schemaLocation' % XSI_NS] = "info:lc/xmlns/premis-v2 ../schemas/premis-v2-2.xsd"

        premis_ids = []
        for top, dirs, files in os.walk('./data/content'):
            for nm in files:
                file_name = os.path.join(top,nm)
                hash = self.sha256(file_name)
                file_url = unicode(os.path.join("file://",file_name), "utf-8")
                fmt = self.fid.identify_file(os.path.abspath(remove_protocol(file_url)))
                jhove = None
                if enable_jhove == True:
                    try:
                        result = self.runCommand(["/usr/bin/jhove", "-h", "xml", os.path.abspath(remove_protocol(file_url))] )
                        if result[0] == 0:
                            jhove = etree.XML(result[1], parser=jhove_parser)
                    except Exception:
                        pass

                size = os.path.getsize(file_name)
                premis_id = uuid.uuid1()
                premis_ids.append(premis_id)
                premis.append(
                    P.object(
                        {q(XSI_NS, 'type'): 'file', "xmlID":premis_id},
                        P.objectIdentifier(
                            P.objectIdentifierType('LOCAL'),
                            P.objectIdentifierValue(premis_id)
                        ),
                        P.objectIdentifier(
                            P.objectIdentifierType('FILEPATH'),
                            P.objectIdentifierValue(file_url)
                        ),
                        P.objectCharacteristics(
                            P.compositionLevel(0),
                            P.size(size),
                            P.fixity(
                                P.messageDigestAlgorithm("SHA-256"),
                                P.messageDigest(hash),
                                P.messageDigestOriginator("hashlib")
                            ),
                            P.format(
                                P.formatRegistry(
                                    P.formatRegistryName("PRONOM"),
                                    P.formatRegistryKey(fmt),
                                    P.formatRegistryRole("identification")
                                )
                            ),
                            #P.objectCharacteristicsExtension(
                                #TODO:// generate id or reference from somewhere
                            #    P.mdSec({"ID":"ID426087e8-0f79-11e3-847a-34e6d700c47b"},
                            #        P.mdWrap({"MDTYPE":"OTHER", "OTHERMDTYPE":"JHOVE"},
                            #            P.xmlData(
                            #                jhove
                            #                 )
                            #                 )
                            #)
                        ),
                    )
                )

        identifier_value = 'earkweb'
        premis.append(P.agent(
                P.agentIdentifier(
                    P.agentIdentifierType('LOCAL'),
                    P.agentIdentifierValue(identifier_value)
                ),
                P.agentName('E-ARK AIP to DIP Converter'),
                P.agentType('Software')))

        identifier_value = 'AIP Creation'
        linking_agent = 'earkweb'
        linking_object=None
        premis.append(P.event(
                P.eventIdentifier(
                    P.eventIdentifierType('LOCAL'),
                    P.eventIdentifierValue(identifier_value)
                ),
                P.eventType,
                P.eventDateTime(datetime.utcnow().isoformat()),
                P.linkingAgentIdentifier(
                    P.linkingAgentIdentifierType('LOCAL'),
                    P.linkingAgentIdentifierValue(linking_agent)
                ),

                P.linkingAgentIdentifier(
                    P.linkingAgentIdentifierType('LOCAL'),
                    P.linkingAgentIdentifierValue(linking_object)
                )
                if linking_object is not None else None
            ))

        str = etree.tostring(premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        path_premis = os.path.join('./metadata/','premis.xml')
        with open(path_premis, 'w') as output_file:
            output_file.write(str)

        return premis_ids

    def createMets(self, premis_ids = None):
        if premis_ids == None:
            premis_ids = self.createPremis()

        #create METS skeleton
        METS_ATTRIBUTES = {"OBJID" : "", "TYPE" : "", "LABEL" : "", "PROFILE" : "http://www.ra.ee/METS/v01/IP.xml", "ID" : "" }
        root = M.mets(METS_ATTRIBUTES)
        root.attrib['{%s}schemaLocation' % XSI_NS] = "http://www.loc.gov/METS/ schemas/IP.xsd ExtensionMETS schemas/ExtensionMETS.xsd http://www.w3.org/1999/xlink schemas/xlink.xsd"

        mets_hdr = M.metsHdr({"CREATEDATE": ts_date(DT_ISO_FORMAT), q(METSEXT_NS,"OAISSTATUS") :"", "RECORDSTATUS" :""})
        root.append(mets_hdr)


        mets_hdr.append(self.createAgent("ARCHIVIST", "ORGANIZATION", "" ,"Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "OTHER", "SOFTWARE", "E-ARK SIP to AIP Converter", "VERSION=0.0.1"))
        mets_hdr.append(self.createAgent("PRESERVATION", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(M.metsDocumentID("METS.xml"))

        mets_dmd = M.dmdSec({"ID":""})
        root.append(mets_dmd)
        # this is how to add descriptive metadata entry
        #file_name = "../schemas/ead.xml"
        #file_url = unicode(os.path.join("file://",file_name), "utf-8")
        #checksum = self.sha256(file_name)
        #file_size = os.path.getsize(file_name)
        #mets_mdref= M.mdRef({"LOCTYPE":"URL", "MDTYPE":"EAD", "MIMETYPE":"text/xml", "CREATED":datetime.utcnow().isoformat(), q(XLINK_NS,"type"):"simple", q(XLINK_NS,"href"):file_url, "CHECKSUMTYPE":"SHA-256", "CHECKSUM":file_checksum, "SIZE":file_size})
        #mets_dmd.append(mets_mdref)

        mets_amdSec = M.amdSec({"ID":"ID" + uuid.uuid1().__str__()})
        root.append(mets_amdSec)

        mets_techmd = M.techMD({"ID":"ID" + uuid.uuid1().__str__()})
        mets_amdSec.append(mets_techmd)
        for id in premis_ids:
            mets_mdref = M.mdRef({"LOCTYPE":"URL", "MDTYPE":"PREMIS:OBJECT", q(XLINK_NS,"href"):"file://./Metadata/PREMIS.xml#"+id.__str__()})
            mets_techmd.append(mets_mdref)

        mets_fileSec = M.fileSec()
        root.append(mets_fileSec)

        mets_filegroup = M.fileGrp({"ID": "ID" + uuid.uuid1().__str__()})
        mets_fileSec.append(mets_filegroup)

        content_ids = self.addFiles("./data/content", mets_filegroup)
        metadata_ids = self.addFiles("./metadata", mets_filegroup)

        mets_structmap = M.structMap({"ID": "", "TYPE":"", "LABEL":"Simple grouping"})
        root.append(mets_structmap)

        mets_structmap_div = M.div({"ADMID":"", "LABEL":"Package", "DMDID" : ""})
        mets_structmap.append(mets_structmap_div)

        mets_structmap_content_div = M.div({"LABEL":"Content"})
        mets_structmap_div.append(mets_structmap_content_div)
        for id in content_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_content_div.append(fptr)

        mets_structmap_metadata_div = M.div({"LABEL":"Metadata"})
        mets_structmap_div.append(mets_structmap_metadata_div)
        for id in metadata_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_metadata_div.append(fptr)

        #my_mets.fileSec.append(M.fileGrp({'USE': 'submission'}))
        #my_mets.fileSec(M.fileGrp({'USE': 'submission'}))
        #mets_schema_file = os.path.join(root_dir, "sandbox/sipgenerator/resources/ENA_RK_TartuLV_141127/schemas/IP_CS_mets.xsd")
        #mets_schema = etree.parse(mets_schema_file)
        #mets_xsd = etree.XMLSchema(mets_schema)

        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

        path_mets = os.path.join('./','METS.xml')
        with open(path_mets, 'w') as output_file:
            output_file.write(str)

class testFormatIdentification(unittest.TestCase):
    def testCreateMetsAndPremis(self):
        print "Working in rootdir %s" % root_dir
        os.chdir(os.path.join(root_dir, "sandbox/sipgenerator/resources/ENA_RK_TartuLV_141127"))
        print "Working in rootdir %s" % os.getcwd()
        sipgen = SIPGenerator()
        sipgen.createMets()


if __name__ == '__main__':
    unittest.main()