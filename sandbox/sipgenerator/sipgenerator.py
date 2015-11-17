from sqlalchemy.sql.functions import char_length

__author__ = 'bartham'

import os

from lxml import etree, objectify
import unittest
import hashlib
import uuid
from mimetypes import MimeTypes

from config.config import root_dir
from subprocess import Popen, PIPE
from earkcore.utils.datetimeutils import current_timestamp, DT_ISO_FMT_SEC_PREC, get_file_ctime_iso_date_str

from earkcore.format.formatidentification import FormatIdentification
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
DELIVERY_METS_NSMAP = { None: METS_NS, "xlink" : "http://www.w3.org/1999/xlink", "xsi" : "http://www.w3.org/2001/XMLSchema-instance" }

M = objectify.ElementMaker(
    annotate=False,
    namespace=METS_NS,
    nsmap=METS_NSMAP)

class SIPGenerator(object):
    fid = FormatIdentification()
    mime = MimeTypes()
    root_path = ""

    def __init__(self, root_path):
        print "Working in rootdir %s" % root_path
        self.root_path = root_path

    def sha256(self, fname):
        hash = hashlib.sha256()
        with open(fname) as f:
            for chunk in iter(lambda: f.read(4096), ""):
                hash.update(chunk)
        return hash.hexdigest()

    def createAgent(self,role, type, other_type, name, note):
        if other_type:
            agent = M.agent({"ROLE":role,"TYPE":type, "OTHERTYPE": other_type}, M.name(name), M.note(note))
        else:
            agent = M.agent({"ROLE":role,"TYPE":type}, M.name(name), M.note(note))
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

    def addFile(self, file_name, mets_filegroup):
        #reload(sys)
        #sys.setdefaultencoding('utf8')
        file_url = "file://./%s" % os.path.relpath(file_name, self.root_path)
        file_mimetype,_ = self.mime.guess_type(file_url)
        file_checksum = self.sha256(file_name)
        file_size = os.path.getsize(file_name)
        file_cdate = get_file_ctime_iso_date_str(file_name, DT_ISO_FMT_SEC_PREC)
        file_id = "ID"+uuid.uuid4().__str__()
        mets_file = M.file({"MIMETYPE":file_mimetype, "CHECKSUMTYPE":"SHA-256", "CREATED":file_cdate, "CHECKSUM":file_checksum, "USE":"Datafile", "ID":file_id, "SIZE":file_size})
        mets_filegroup.append(mets_file)
        #_,fname = os.path.split(file_name)
        mets_FLocat = M.FLocat({q(XLINK_NS, 'href'): file_url, "LOCTYPE":"URL", q(XLINK_NS, 'type'): 'simple'})
        mets_file.append(mets_FLocat)
        return file_id

    def addFiles(self, folder, mets_filegroup):
        ids = []
        for top, dirs, files in os.walk(folder):
            for fn in files:
                file_name = os.path.join(top, fn)
                file_id = self.addFile(file_name,mets_filegroup)
                ids.append(file_id)
        return ids

    def createPremis(self, enable_jhove = False):
        jhove_parser = None
        if enable_jhove == True:
            jhove_parser = etree.XMLParser(remove_blank_text=True)

        PREMIS_ATTRIBUTES = {"version" : "2.0"}
        premis = P.premis(PREMIS_ATTRIBUTES)
        premis.attrib['{%s}schemaLocation' % XSI_NS] = "info:lc/xmlns/premis-v2 ../../schemas/premis-v2-2.xsd"

        premis_ids = []
        for top, dirs, files in os.walk(os.path.join(self.root_path, 'data')):
            for nm in files:
                file_name = os.path.join(top,nm)
                hash = self.sha256(file_name)
                file_url = "file://./%s" % os.path.relpath(file_name, self.root_path)
                fmt = self.fid.identify_file(file_name)#os.path.abspath(remove_protocol(file_url)))
                jhove = None
                if enable_jhove == True:
                    try:
                        result = self.runCommand(["/usr/bin/jhove", "-h", "xml", file_name] )
                        if result[0] == 0:
                            jhove = etree.XML(result[1], parser=jhove_parser)
                    except Exception:
                        #TODO: handle exception
                        pass

                size = os.path.getsize(file_name)
                premis_id = uuid.uuid4()
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
                P.eventDateTime(current_timestamp()),
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
        preservation_dir = os.path.join(self.root_path,'./metadata/preservation')
        if not os.path.exists(preservation_dir):
            os.mkdir(preservation_dir)
        path_premis = os.path.join(self.root_path,'./metadata/preservation/premis.xml')
        with open(path_premis, 'w') as output_file:
            output_file.write(str)

        return premis_ids

    def createSIPMets(self, premis_ids = None):
        #if premis_ids == None:
        #    premis_ids = self.createPremis()

        #create METS skeleton
        # METS_ATTRIBUTES = {"OBJID" : "", "TYPE" : "", "LABEL" : "", "PROFILE" : "http://www.ra.ee/METS/v01/IP.xml", "ID" : "" }
        METS_ATTRIBUTES = {"OBJID": "placeholder123",
                           "LABEL": "METS file describing the SIP matching the OBJID.",
                           "PROFILE": "http://www.ra.ee/METS/v01/IP.xml",
                           "TYPE": "SIP"}
        root = M.mets(METS_ATTRIBUTES)
        root.attrib['{%s}schemaLocation' % XSI_NS] = "http://www.loc.gov/METS/ schemas/IP.xsd ExtensionMETS schemas/ExtensionMETS.xsd http://www.w3.org/1999/xlink schemas/xlink.xsd"

        # mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp(), q(METSEXT_NS,"OAISSTATUS") :"", "RECORDSTATUS" :""})
        mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp(), "RECORDSTATUS" :"NEW"})
        root.append(mets_hdr)


        mets_hdr.append(self.createAgent("ARCHIVIST", "ORGANIZATION", "" ,"Institution", "Note"))
        mets_hdr.append(self.createAgent("ARCHIVIST", "OTHER", "" ,"Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "OTHER", "SOFTWARE", "E-ARK SIP Creator", "VERSION=0.0.1"))
        mets_hdr.append(self.createAgent("PRESERVATION", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(M.metsDocumentID("METS.xml"))

        mets_dmd = M.dmdSec({"ID": "ID" + uuid.uuid4().__str__()})
        root.append(mets_dmd)
        # this is how to add descriptive metadata entry
        #file_name = "../schemas/ead.xml"
        #file_url = unicode(os.path.join("file://",file_name), "utf-8")
        #checksum = self.sha256(file_name)
        #file_size = os.path.getsize(file_name)
        #mets_mdref= M.mdRef({"LOCTYPE":"URL", "MDTYPE":"EAD", "MIMETYPE":"text/xml", "CREATED":current_timestamp(), q(XLINK_NS,"type"):"simple", q(XLINK_NS,"href"):file_url, "CHECKSUMTYPE":"SHA-256", "CHECKSUM":file_checksum, "SIZE":file_size})
        #mets_dmd.append(mets_mdref)

        mets_amdSec = M.amdSec({"ID":"ID" + uuid.uuid4().__str__()})
        root.append(mets_amdSec)

        mets_techmd = M.techMD({"ID":"ID" + uuid.uuid4().__str__()})
        mets_amdSec.append(mets_techmd)
        #for id in premis_ids:
        #    mets_mdref = M.mdRef({"LOCTYPE":"URL", "MDTYPE":"PREMIS:OBJECT", q(XLINK_NS,"href"):"file://./metadata/preservation/PREMIS.xml#"+id.__str__()})
        #    mets_techmd.append(mets_mdref)
        #techmd_ids = self.addFiles(os.path.join(self.root_path, 'metadata/preservation'))


        mets_fileSec = M.fileSec()
        root.append(mets_fileSec)

        # general filegroup
        mets_filegroup = M.fileGrp({"ID": "ID" + uuid.uuid4().__str__(), "USE": "general filegroup"})
        mets_fileSec.append(mets_filegroup)

        # data, metadata and schemas - package level
        content_ids = self.addFiles(os.path.join(self.root_path, 'data'), mets_filegroup)
        metadata_ids = self.addFiles(os.path.join(self.root_path, 'metadata'), mets_filegroup)
        schema_ids = self.addFiles(os.path.join(self.root_path, 'schemas'), mets_filegroup)

        # checking for cross-representation metadata and schemas:
        package_root = self.root_path.rsplit('/', 2)
        package_metadata = os.path.join(package_root[0], 'metadata')
        cross_metadata_ids = self.addFiles(package_metadata, mets_filegroup)
        package_schemas = os.path.join(package_root[0], 'schemas')
        cross_schemas_ids = self.addFiles(package_schemas, mets_filegroup)

        # mets_structmap = M.structMap({"ID": "", "TYPE":"", "LABEL":"Simple grouping"})
        mets_structmap = M.structMap({"LABEL": "Simple SIP structuring", "TYPE": "logical"})
        root.append(mets_structmap)

        mets_structmap_div = M.div({"ADMID":"", "LABEL":"Package", "DMDID" : ""})
        mets_structmap.append(mets_structmap_div)

        # files in /data
        mets_structmap_content_div = M.div({"LABEL":"Content"})
        mets_structmap_div.append(mets_structmap_content_div)
        for id in content_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_content_div.append(fptr)

        # files in /metadata and ./../../metadata
        mets_structmap_metadata_div = M.div({"LABEL":"Metadata"})
        mets_structmap_div.append(mets_structmap_metadata_div)
        for id in metadata_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_metadata_div.append(fptr)
        for id in cross_metadata_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_metadata_div.append(fptr)

        # files in /schemas and ./../../schemas
        mets_structmap_schemas_div = M.div({"LABEL": "Schemas"})
        mets_structmap_div.append(mets_structmap_schemas_div)
        for id in schema_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_schemas_div.append(fptr)
        for id in cross_schemas_ids:
            fptr = M.fptr({"FILEID": id})
            mets_structmap_schemas_div.append(fptr)

        #my_mets.fileSec.append(M.fileGrp({'USE': 'submission'}))
        #my_mets.fileSec(M.fileGrp({'USE': 'submission'}))
        #mets_schema_file = os.path.join(root_dir, "sandbox/sipgenerator/resources/ENA_RK_TartuLV_141127/schemas/IP.xsd")
        #mets_schema = etree.parse(mets_schema_file)
        #mets_xsd = etree.XMLSchema(mets_schema)

        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

        path_mets = os.path.join(self.root_path,'METS.xml')
        with open(path_mets, 'w') as output_file:
            output_file.write(str)


    #def createAIPMets(self, premis_ids=None):
    def createAIPMets(self, packageid):
        '''
        Create the AIP METS file.

        @param premis_ids:
        @return:
        '''
        #if premis_ids == None:
        #    premis_ids = self.createPremis()

        # TODO: add metadata files to correct metadata sections!

        # create METS skeleton
        METS_ATTRIBUTES = {"OBJID": packageid,
                           "LABEL": "METS file describing the AIP matching the OBJID.",
                           "PROFILE": "http://www.ra.ee/METS/v01/IP.xml",
                           "TYPE": "AIP"}
        root = M.mets(METS_ATTRIBUTES)
        root.attrib['{%s}schemaLocation' % XSI_NS] = "http://www.loc.gov/METS/ schemas/IP.xsd ExtensionMETS schemas/ExtensionMETS.xsd http://www.w3.org/1999/xlink schemas/xlink.xsd"

        # mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp(), q(METSEXT_NS,"OAISSTATUS") :"", "RECORDSTATUS" :"AIP"})
        mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp(), "RECORDSTATUS" :"NEW"})
        root.append(mets_hdr)

        mets_hdr.append(self.createAgent("ARCHIVIST", "ORGANIZATION", "" ,"Institution", "Note"))
        mets_hdr.append(self.createAgent("ARCHIVIST", "OTHER", "" ,"Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "OTHER", "SOFTWARE", "E-ARK SIP Creator", "VERSION=0.0.1"))
        mets_hdr.append(self.createAgent("PRESERVATION", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(M.metsDocumentID("METS.xml"))

        mets_dmd = M.dmdSec({"ID": "ID" + uuid.uuid4().__str__()})
        root.append(mets_dmd)
        # this is how to add descriptive metadata entry
        #file_name = "../schemas/ead.xml"
        #file_url = unicode(os.path.join("file://",file_name), "utf-8")
        #checksum = self.sha256(file_name)
        #file_size = os.path.getsize(file_name)
        #mets_mdref= M.mdRef({"LOCTYPE":"URL", "MDTYPE":"EAD", "MIMETYPE":"text/xml", "CREATED":current_timestamp(), q(XLINK_NS,"type"):"simple", q(XLINK_NS,"href"):file_url, "CHECKSUMTYPE":"SHA-256", "CHECKSUM":file_checksum, "SIZE":file_size})
        #mets_dmd.append(mets_mdref)

        # create amdSec
        mets_amdSec = M.amdSec({"ID": "ID" + uuid.uuid4().__str__()})
        root.append(mets_amdSec)

        # create techMD
        #mets_techmd = M.techMD({"ID": "ID" + uuid.uuid4().__str__()})
        #mets_amdSec.append(mets_techmd)
        #for id in premis_ids:
        #    mets_mdref = M.mdRef({"LOCTYPE":"URL", "MDTYPE":"PREMIS:OBJECT", q(XLINK_NS,"href"):"file://./metadata/preservation/PREMIS.xml#"+id.__str__()})
        #    mets_techmd.append(mets_mdref)

        mets_fileSec = M.fileSec()
        root.append(mets_fileSec)

        # TODO: metadata entries into correct mets section + structmap: seperate between AIP and rep level metadata!
        # check if there is another METS file referencing the metadata

        # general filegroup
        mets_filegroup = M.fileGrp({"ID": "ID" + uuid.uuid4().__str__(), "USE": "general filegroup"})
        mets_fileSec.append(mets_filegroup)

        #metadata_ids = self.addFiles(os.path.join(self.root_path, 'metadata'), mets_filegroup)
        #submission_meta_ids = self.addFiles(os.path.join(self.root_path, 'submission/metadata'), mets_filegroup)

        # mets_structmap = M.structMap({"ID": "", "TYPE":"", "LABEL":"Simple grouping"})
        mets_structmap = M.structMap({"LABEL": "Simple AIP structuring", "TYPE": "logical"})
        root.append(mets_structmap)

        mets_structmap_div = M.div({"ADMID":"", "LABEL":"Package", "DMDID" : ""})
        mets_structmap.append(mets_structmap_div)

        # metadata structmap - IP root level!
        mets_structmap_metadata_div = M.div({"LABEL": "Metadata AIP"})
        mets_structmap_div.append(mets_structmap_metadata_div)
        #for id in metadata_ids:
        #    fptr = M.fptr({"FILEID": id})
        #    mets_structmap_metadata_div.append(fptr)

        # metadata structmap - submission level!
        mets_structmap_metadata_sub_div = M.div({"LABEL": "Metadata Submission"})
        mets_structmap_div.append(mets_structmap_metadata_sub_div)
        #for id in submission_meta_ids:
        #    fptr = M.fptr({"FILEID": id})
        #    mets_structmap_metadata_sub_div.append(fptr)

        # content structmap - all representations! (is only filled if no separate METS exists for the rep)
        mets_structmap_content_div = M.div({"LABEL": "various files"})
        mets_structmap_div.append(mets_structmap_content_div)

        # structmap for schema files
        mets_structmap_schema_div = M.div({"LABEL": "schema files"})
        mets_structmap_div.append(mets_structmap_schema_div)

        # create structmap for representations
        # mets_structmap_reps = M.structMap({"ID": "", "TYPE":"", "LABEL":"representations"})
        mets_structmap_reps = M.structMap({"TYPE":"logical", "LABEL":"representations"})
        root.append(mets_structmap_reps)
        mets_div_reps = M.div({'LABEL': 'representations', 'TYPE': 'type'})
        mets_structmap_reps.append(mets_div_reps)

        # package
        workdir_length = len(self.root_path)
        #for directory, subdirectories, filenames in os.walk(os.path.join(self.root_path, 'submission/representations')):
        for directory, subdirectories, filenames in os.walk(self.root_path):
            if len(filenames) > 0:
                for filename in filenames:
                    # ignore all files on AIP root level (since they wont be packed with the AIP):
                    if directory == self.root_path:
                        del filename
                    else:
                        rel_path_file = ('file://.' + directory[workdir_length:] + '/' + filename).decode('utf-8')
                        if filename.lower() == 'mets.xml':
                            # delete the subdirectories list to stop os.walk from traversing further;
                            # mets file should be added as <mets:mptr> to <structMap> for corresponding rep
                            del subdirectories[:]
                            rep_name = directory.rsplit('/', 2)
                            rep_name = os.path.join(rep_name[1], rep_name[2])
                            # create structMap div and append to representations structMap
                            mets_structmap_rep_div = M.div({"LABEL": rep_name, "TYPE": "representation mets"})
                            mets_div_reps.append(mets_structmap_rep_div)
                            # add mets file as <mets:mptr>
                            metspointer = M.mptr({"LOCTYPE": "URL",
                                                  q(XLINK_NS,"title"): "mets file describing representation: " + rep_name + " of AIP: " + packageid,
                                                  q(XLINK_NS,"href"): rel_path_file})
                            mets_structmap_rep_div.append(metspointer)
                            # also add the rep mets to the filegroup, so we can have a fptr
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            mets_fptr = M.fptr({"FILEID": id})
                            mets_structmap_rep_div.append(mets_fptr)
                        elif filename and directory.endswith('schemas'):
                            # schema files
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            fptr = M.fptr({'FILEID': id})
                            mets_structmap_schema_div.append(fptr)
                        elif filename == 'earkweb.log':
                            # earkweb log file - currently treated as digiprovMD
                            mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                            mets_amdSec.append(mets_digiprovmd)
                            checksum = self.sha256(os.path.join(directory,filename))
                            mets_mdref = M.mdRef({"LOCTYPE":"URL",
                                                 "MIMETYPE":"text/xml",
                                                 "CREATED":current_timestamp(),
                                                 q(XLINK_NS,"type"):"simple",
                                                 q(XLINK_NS,"href"):rel_path_file,
                                                 "CHECKSUMTYPE":"SHA-256",
                                                 "CHECKSUM":checksum})
                            mets_digiprovmd.append(mets_mdref)
                        elif filename and not (directory.endswith('descriptive') or
                                               directory.endswith('metadata')):
                            # how to handle submission/metadata files?
                            # print 'found a file: ' + os.path.join(directory, filename)
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            fptr = M.fptr({"FILEID": id})
                            mets_structmap_content_div.append(fptr)


        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

        path_mets = os.path.join(self.root_path,'METS.xml')
        with open(path_mets, 'w') as output_file:
            output_file.write(str)


    def createDeliveryMets(self, input_archive, output_mets):
        #create delivery METS skeleton
        METS_ATTRIBUTES = {"OBJID" : "UUID:" + uuid.uuid4().__str__(), "TYPE" : "SIP", "LABEL" : "Delivery METS", "PROFILE" : "http://webb.eark/package/METS/IP_CS.xml", "ID" : "ID" + uuid.uuid4().__str__() }
        root = M.mets(METS_ATTRIBUTES)
        root.attrib['{%s}schemaLocation' % XSI_NS] = "http://www.loc.gov/METS/ schemas/IP.xsd"

        mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp()})
        root.append(mets_hdr)


        mets_hdr.append(self.createAgent("ARCHIVIST", "ORGANIZATION", "" ,"Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "ORGANIZATION", "", "Institution", "Note"))
        mets_hdr.append(self.createAgent("CREATOR", "OTHER", "SOFTWARE", "E-ARK SIP Creator", "VERSION=0.0.1"))
        mets_hdr.append(self.createAgent("PRESERVATION", "ORGANIZATION", "", "Institution", "Note"))
        _,fname = os.path.split(output_mets)
        mets_hdr.append(M.metsDocumentID(fname))

        mets_fileSec = M.fileSec()
        root.append(mets_fileSec)

        mets_filegroup = M.fileGrp({"USE" : "PACKAGES", "ID": "ID" + uuid.uuid4().__str__()})
        mets_fileSec.append(mets_filegroup)

        content_id = self.addFile(input_archive, mets_filegroup)

        mets_structmap = M.structMap({"ID": "ID%s" % uuid.uuid4(), "TYPE": "physical", "LABEL": "Profilestructmap"})
        root.append(mets_structmap)
        mets_structmap_div = M.div({"LABEL": "Package"})
        mets_structmap.append(mets_structmap_div)
        mets_structmap_content_div = M.div({"LABEL": "Content"})
        mets_structmap_div.append(mets_structmap_content_div)
        fptr = M.fptr({"FILEID": "ID%s" % uuid.uuid4()})
        mets_structmap_content_div.append(fptr)

        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        with open(output_mets, 'w') as output_file:
            output_file.write(str)


class testFormatIdentification(unittest.TestCase):
    def testCreateMetsAndPremis(self):
        sipgen = SIPGenerator(os.path.join(root_dir, "sandbox/sipgenerator/resources/ENA_RK_TartuLV_141127"))
        #input_folder = os.path.join(root_dir, "sandbox/sipgenerator/resources/ENA_RK_TartuLV_141127")
        #output_mets = os.path.join(root_dir, "sandbox/sipgenerator/resources/ENA_RK_TartuLV_141127/metadata/METS.xml")
        sipgen.createSIPMets()

    def atestCreateDeliveryMets(self):
        sipgen = SIPGenerator(os.path.join(root_dir, "sandbox/sipgenerator/resources/"))
        input_archive = os.path.join(root_dir, "sandbox/sipgenerator/resources/test.tar")
        output_mets = os.path.join(root_dir, "sandbox/sipgenerator/resources/delivery_METS.xml")
        sipgen.createDeliveryMets(input_archive, output_mets)


if __name__ == '__main__':
    unittest.main()