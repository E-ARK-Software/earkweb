import os
from lxml import etree, objectify
import unittest
import uuid
from mimetypes import MimeTypes
from subprocess import Popen, PIPE
from earkcore.utils.datetimeutils import current_timestamp, DT_ISO_FMT_SEC_PREC, get_file_ctime_iso_date_str
from earkcore.format.formatidentification import FormatIdentification
from earkcore.metadata.XmlHelper import q, XSI_NS
import fnmatch
from earkcore.fixity.ChecksumFile import get_sha256_hash

METS_NS = 'http://www.loc.gov/METS/'
METSEXT_NS = 'ExtensionMETS'
XLINK_NS = "http://www.w3.org/1999/xlink"
METS_NSMAP = {None: METS_NS, "xlink": "http://www.w3.org/1999/xlink", "ext": METSEXT_NS,
              "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
DELIVERY_METS_NSMAP = {None: METS_NS, "xlink": "http://www.w3.org/1999/xlink",
                       "xsi": "http://www.w3.org/2001/XMLSchema-instance"}

M = objectify.ElementMaker(
    annotate=False,
    namespace=METS_NS,
    nsmap=METS_NSMAP)


class MetsGenerator(object):
    '''
    This class generates a Mets file.
    It has to be instantiated (something = MetsGenerator(path) with the (A/S)IP root path as an argument (to specify
    the Mets directory; all subfolders will be treated as part of the IP. After this. the createMets can be called
    (something.createMets(data)) with a dictionary that must contain 'packageid', 'schemas' (location of the schema
    folder) and 'type', where 'type' must comply with the Mets standard for TYPE attribute of the Mets root.
    '''

    fid = FormatIdentification()
    mime = MimeTypes()
    root_path = ""
    mets_data = None

    def __init__(self, root_path):
        print "Working in rootdir %s" % root_path
        self.root_path = root_path

    def runCommand(self, program, stdin=PIPE, stdout=PIPE, stderr=PIPE):
        result, res_stdout, res_stderr = None, None, None
        try:
            # quote the executable otherwise we run into troubles
            # when the path contains spaces and additional arguments
            # are presented as well.
            # special: invoking bash as login shell here with
            # an unquoted command does not execute /etc/profile

            print 'Launching: ' + ' '.join(program)
            process = Popen(program, stdin=stdin, stdout=stdout, stderr=stderr, shell=False)

            res_stdout, res_stderr = process.communicate()
            result = process.returncode
            print 'Finished: ' + ' '.join(program)

        except Exception as ex:
            res_stderr = ''.join(str(ex.args))
            result = 1

        if result != 0:
            print 'Command failed:' + ''.join(res_stderr)
            raise Exception('Command failed:' + ''.join(res_stderr))

        return result, res_stdout, res_stderr

    def createAgent(self,role, type, other_type, name, note):
        if other_type:
            agent = M.agent({"ROLE": role, "TYPE": type, "OTHERTYPE": other_type}, M.name(name), M.note(note))
        else:
            agent = M.agent({"ROLE": role, "TYPE": type}, M.name(name), M.note(note))
        return agent

    def addFile(self, file_name, mets_filegroup):
        # reload(sys)
        # sys.setdefaultencoding('utf8')
        file_url = "file://./%s" % os.path.relpath(file_name, self.root_path)
        file_mimetype, _ = self.mime.guess_type(file_url)
        file_checksum = get_sha256_hash(file_name)
        file_size = os.path.getsize(file_name)
        file_cdate = get_file_ctime_iso_date_str(file_name, DT_ISO_FMT_SEC_PREC)
        file_id = "ID" + uuid.uuid4().__str__()
        mets_file = M.file(
            {"MIMETYPE": file_mimetype, "CHECKSUMTYPE": "SHA-256", "CREATED": file_cdate, "CHECKSUM": file_checksum,
             "USE": "Datafile", "ID": file_id, "SIZE": file_size})
        mets_filegroup.append(mets_file)
        # _,fname = os.path.split(file_name)
        mets_FLocat = M.FLocat({q(XLINK_NS, 'href'): file_url, "LOCTYPE": "URL", q(XLINK_NS, 'type'): 'simple'})
        mets_file.append(mets_FLocat)
        return file_id

    def addFiles(self, folder, mets_filegroup):
        ids = []
        for top, dirs, files in os.walk(folder):
            for fn in files:
                file_name = os.path.join(top, fn)
                file_id = self.addFile(file_name, mets_filegroup)
                ids.append(file_id)
        return ids

    def make_mdref(self, path, file, id, mdtype):
        mimetype, _ = self.mime.guess_type(os.path.join(path, file))
        rel_path = "file://./%s" % os.path.relpath(os.path.join(path, file), self.root_path)
        mets_mdref = {"LOCTYPE": "URL",
                      "MIMETYPE": mimetype,
                      "CREATED": current_timestamp(),
                      q(XLINK_NS, "type"): "simple",
                      q(XLINK_NS, "href"): rel_path,
                      "CHECKSUMTYPE": "SHA-256",
                      "CHECKSUM": get_sha256_hash(os.path.join(path, file)),
                      "ID": id,
                      "MDTYPE": mdtype}
        return mets_mdref

    def setParentRelation(self, identifier):
        parentmets = os.path.join(self.root_path, 'METS.xml')
        packagetype = self.mets_data['type']
        if os.path.exists(parentmets):
            parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
            parent_parse = etree.parse(parentmets, parser)
            parent_root = parent_parse.getroot()

            parent = M.div({'LABEL': "parent %s" % packagetype})
            pointer = M.mptr({"LOCTYPE": "OTHER",
                              "OTHERLOCTYPE": "UUID",
                              q(XLINK_NS, "title"): ("Referencing a parent %s." % packagetype),
                              q(XLINK_NS, "href"): "urn:uuid:" + identifier,
                              "ID": "ID" + uuid.uuid4().__str__()})
            parent.append(pointer)

            parent_map = parent_root.find("%s[@LABEL='parent %s']" % (q(METS_NS, 'structMap'), packagetype))
            if parent_map is not None:
                parent_div = parent_map.find("%s[@LABEL='parent %s identifiers']" % (q(METS_NS, 'div'), packagetype))
                parent_div.append(parent)
            else:
                parent_map = M.structMap({'LABEL': 'parent %s' % packagetype, 'TYPE': 'logical'})
                parent_div = M.div({'LABEL': 'parent %s identifiers' % packagetype})
                parent_map.append(parent_div)
                parent_div.append(parent)
                parent_root.insert(len(parent_root), parent_map)

            str = etree.tostring(parent_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
            with open(parentmets, 'w') as output_file:
                output_file.write(str)
        else:
            print 'Couldn\'t find the parent %ss Mets file.' %packagetype

    def addChildRelation(self, identifier):
        parentmets = os.path.join(self.root_path, 'METS.xml')
        packagetype = self.mets_data['type']
        if os.path.exists(parentmets):
            parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
            parent_parse = etree.parse(parentmets, parser)
            parent_root = parent_parse.getroot()
            child = M.div({'LABEL': "child %s" % packagetype})
            pointer = M.mptr({"LOCTYPE": "OTHER",
                              "OTHERLOCTYPE": "UUID",
                              q(XLINK_NS, "title"): ("Referencing a child %s." % packagetype),
                              q(XLINK_NS, "href"): "urn:uuid:" + identifier,
                              "ID": "ID" + uuid.uuid4().__str__()})
            child.append(pointer)

            children_map = parent_root.find("%s[@LABEL='child %s']" % (q(METS_NS, 'structMap'), packagetype))
            if children_map is not None:
                children_div = children_map.find("%s[@LABEL='child %s identifiers']" % (q(METS_NS, 'div'), packagetype))
                children_div.append(child)
            else:
                children_map = M.structMap({'LABEL': 'child %s' % packagetype, 'TYPE': 'logical'})
                children_div = M.div({'LABEL': 'child %s identifiers' % packagetype})
                children_map.append(children_div)
                children_div.append(child)
                parent_root.insert(len(parent_root), children_map)

            str = etree.tostring(parent_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
            with open(parentmets, 'w') as output_file:
                output_file.write(str)
        else:
            print 'Couldn\'t find the parent %ss Mets file.' %packagetype

    def createMets(self, mets_data):
        self.mets_data = mets_data
        packageid = mets_data['packageid']
        packagetype = mets_data['type']
        schemafolder = mets_data['schemas']
        parent = mets_data['parent']

        print 'creating Mets'
        ###########################
        # create METS skeleton
        ###########################

        # create Mets root
        METS_ATTRIBUTES = {"OBJID": "urn:uuid:" + packageid,
                           "LABEL": "METS file describing the %s matching the OBJID." % packagetype,
                           "PROFILE": "http://www.ra.ee/METS/v01/IP.xml",
                           "TYPE": packagetype}
        root = M.mets(METS_ATTRIBUTES)

        if os.path.isfile(os.path.join(schemafolder, 'mets_1_11.xsd')):
            mets_schema_location = os.path.relpath(os.path.join(schemafolder, 'mets_1_11.xsd'), self.root_path)
        else:
            mets_schema_location = 'empty'
        if os.path.isfile(os.path.join(schemafolder, 'xlink.xsd')):
            xlink_schema_loaction = os.path.relpath(os.path.join(schemafolder, 'xlink.xsd'), self.root_path)
        else:
            xlink_schema_loaction = 'empty'

        root.attrib['{%s}schemaLocation' % XSI_NS] = "http://www.loc.gov/METS/ %s http://www.w3.org/1999/xlink %s" % (mets_schema_location, xlink_schema_loaction)

        # create Mets header
        mets_hdr = M.metsHdr({"CREATEDATE": current_timestamp(), "RECORDSTATUS": "NEW"})
        root.append(mets_hdr)

        # add an agent
        mets_hdr.append(self.createAgent("CREATOR", "OTHER", "SOFTWARE", "E-ARK earkweb", "VERSION=0.0.1"))

        # add document ID
        mets_hdr.append(M.metsDocumentID("METS.xml"))

        # create amdSec
        mets_amdSec = M.amdSec({"ID": "ID" + uuid.uuid4().__str__()})
        root.append(mets_amdSec)

        # create fileSec
        mets_fileSec = M.fileSec()
        root.append(mets_fileSec)

        # general filegroup
        mets_filegroup = M.fileGrp({"ID": "ID" + uuid.uuid4().__str__(), "USE": "general filegroup"})
        mets_fileSec.append(mets_filegroup)

        # structMap 'E-ARK structural map' - default, physical structure
        mets_earkstructmap = M.structMap({"LABEL": "E-ARK structural map", "TYPE": "physical"})
        root.append(mets_earkstructmap)
        package_div = M.div({"LABEL": packageid})
        # append physical structMap
        mets_earkstructmap.append(package_div)

        # structMap and div for the whole package (metadata, schema and /data)
        mets_structmap = M.structMap({"LABEL": "Simple %s structuring" % packagetype, "TYPE": "logical"})
        root.append(mets_structmap)
        mets_structmap_div = M.div({"LABEL": "Package structure"})
        mets_structmap.append(mets_structmap_div)

        # metadata structmap - IP root level!
        mets_structmap_metadata_div = M.div({"LABEL": "metadata files"})
        mets_structmap_div.append(mets_structmap_metadata_div)

        # structmap for schema files
        mets_structmap_schema_div = M.div({"LABEL": "schema files"})
        mets_structmap_div.append(mets_structmap_schema_div)

        # content structmap - all representations! (is only filled if no separate METS exists for the rep)
        mets_structmap_content_div = M.div({"LABEL": "content files"})
        mets_structmap_div.append(mets_structmap_content_div)

        # create structmap and div for Mets files from representations
        # mets_structmap_reps = M.structMap({"TYPE": "logical", "LABEL": "representations"})
        # root.append(mets_structmap_reps)
        # mets_div_reps = M.div({"LABEL": "representations", "TYPE": "type"})
        # mets_structmap_reps.append(mets_div_reps)

        # create structmap for parent/child relation, if applicable
        if parent != '':
            print 'creating link to parent %s' % packagetype
            mets_structmap_relation = M.structMap({'TYPE': 'logical', 'LABEL': 'parent'})
            root.append(mets_structmap_relation)
            mets_div_rel = M.div({'LABEL': '%s parent identifier' % packagetype})
            mets_structmap_relation.append(mets_div_rel)
            parent_pointer = M.mptr({"LOCTYPE": "OTHER",
                                     "OTHERLOCTYPE": "UUID",
                                     q(XLINK_NS, "title"): ("Referencing the parent %s of this (urn:uuid:%s) %s." % (packagetype, packageid, packagetype)),
                                     q(XLINK_NS, "href"): "urn:uuid:" + parent,
                                     "ID": "ID" + uuid.uuid4().__str__()})
            mets_div_rel.append(parent_pointer)

        ###########################
        # add to Mets skeleton
        ###########################

        # add the package content to the Mets skeleton
        for directory, subdirectories, filenames in os.walk(self.root_path):
            # build the earkstructmap
            path = os.path.relpath(directory, self.root_path)
            physical_div = ''
            if path != '.':
                physical_div = M.div({"LABEL": path})
                package_div.append(physical_div)
            # if directory.endswith('metadata/earkweb'):
            #     # Ignore temp files only needed for IP processing with earkweb
            #     del filenames[:]
            #     del subdirectories[:]
            if directory.endswith('submission/metadata') or directory.endswith('submission/schemas'):
                del filenames[:]
                del subdirectories[:]
            if directory == os.path.join(self.root_path, 'metadata'):
                # Metadata on IP root level - if there are folders for representation-specific metadata,
                # check if the corresponding representation has a Mets file. If yes, skip; if no, add to IP root Mets.
                for filename in filenames:
                    if filename == 'earkweb.log':
                        mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                        mets_amdSec.append(mets_digiprovmd)
                        id = "ID" + uuid.uuid4().__str__()
                        ref = self.make_mdref(directory, filename, id, 'OTHER')
                        mets_mdref = M.mdRef(ref)
                        mets_digiprovmd.append(mets_mdref)
                        mets_structmap_metadata_div.append(M.fptr({"FILEID": id}))
                        physical_div.append(M.fptr({"FILEID": id}))
                del subdirectories[:]  # prevent loop to iterate subfolders outside of this if statement
                dirlist = os.listdir(os.path.join(self.root_path, 'metadata'))
                for dirname in dirlist:
                    if fnmatch.fnmatch(dirname, '*_mig-*'):
                        # TODO: maybe list it all the time?
                        # this folder contains metadata for a representation/migration, currently:
                        # only listed if no representation Mets file exists
                        if os.path.isfile(os.path.join(self.root_path, 'representations/%s/METS.xml') % dirname):
                            pass
                        else:
                            for dir, subdir, files in os.walk(os.path.join(self.root_path, 'metadata/%s') % dirname):
                                for filename in files:
                                    if dir.endswith('descriptive'):
                                        mets_dmd = M.dmdSec({"ID": "ID" + uuid.uuid4().__str__()})
                                        root.insert(1, mets_dmd)
                                        id = "ID" + uuid.uuid4().__str__()
                                        ref = self.make_mdref(dir, filename, id, 'OTHER')
                                        mets_mdref = M.mdRef(ref)
                                        mets_dmd.append(mets_mdref)
                                        mets_structmap_metadata_div.append(M.fptr({"FILEID": id}))
                                        physical_div.append(M.fptr({"FILEID": id}))
                                    elif dir.endswith('preservation'):
                                        mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                                        mets_amdSec.append(mets_digiprovmd)
                                        id = "ID" + uuid.uuid4().__str__()
                                        mdtype = ''
                                        if filename.startswith('premis') or filename.endswith('premis.xml'):
                                            mdtype = 'PREMIS'
                                        else:
                                            mdtype = 'OTHER'
                                        ref = self.make_mdref(dir, filename, id, mdtype)
                                        mets_mdref = M.mdRef(ref)
                                        mets_digiprovmd.append(mets_mdref)
                                        mets_structmap_metadata_div.append(M.fptr({"FILEID": id}))
                                        physical_div.append(M.fptr({"FILEID": id}))
                                    elif filename:
                                        print 'Unclassified metadata file %s in %s.' % (filename, dir)
                    else:
                        # metadata that should be listed in the Mets
                        for dir, subdir, files in os.walk(os.path.join(self.root_path, 'metadata/%s') % dirname):
                            if len(files) > 0:
                                for filename in files:
                                    #if dir.endswith('descriptive'):
                                    if dirname == 'descriptive':
                                        mets_dmd = M.dmdSec({"ID": "ID" + uuid.uuid4().__str__()})
                                        root.insert(1, mets_dmd)
                                        id = "ID" + uuid.uuid4().__str__()
                                        # TODO: change MDTYPE
                                        ref = self.make_mdref(dir, filename, id, 'OTHER')
                                        mets_mdref = M.mdRef(ref)
                                        mets_dmd.append(mets_mdref)
                                        mets_structmap_metadata_div.append(M.fptr({"FILEID": id}))
                                        physical_div.append(M.fptr({"FILEID": id}))
                                    #elif dir.endswith('preservation'):
                                    elif dirname == 'preservation' or dirname == 'earkweb':
                                        mets_digiprovmd = M.digiprovMD({"ID": "ID" + uuid.uuid4().__str__()})
                                        mets_amdSec.append(mets_digiprovmd)
                                        id = "ID" + uuid.uuid4().__str__()
                                        mdtype = ''
                                        if filename.startswith('premis') or filename.endswith('premis.xml'):
                                            mdtype = 'PREMIS'
                                        elif filename:
                                            mdtype = 'OTHER'
                                        ref = self.make_mdref(dir, filename, id, mdtype)
                                        mets_mdref = M.mdRef(ref)
                                        mets_digiprovmd.append(mets_mdref)
                                        mets_structmap_metadata_div.append(M.fptr({"FILEID": id}))
                                        physical_div.append(M.fptr({"FILEID": id}))
                                    elif filename:
                                        print 'Unclassified metadata file %s in %s.' % (filename, dir)
            else:
                # Any other folder outside of /<root>/metadata
                for filename in filenames:
                    if directory == self.root_path:
                        # ignore files on IP root level
                        del filename
                    else:
                        # TODO: list rep metadata only in the rep Mets?
                        rel_path_file = "file://./%s" % os.path.relpath(os.path.join(directory, filename), self.root_path)
                        if filename.lower() == 'mets.xml':
                            # delete the subdirectories list to stop os.walk from traversing further;
                            # mets file should be added as <mets:mptr> to <structMap> for corresponding rep
                            del subdirectories[:]
                            rep_name = directory.rsplit('/', 1)[1]
                            # create structMap div and append to representations structMap
                            # mets_structmap_rep_div = M.div({"LABEL": rep_name, "TYPE": "representation mets", "ID": "ID" + uuid.uuid4().__str__()})
                            # mets_div_reps.append(mets_structmap_rep_div)
                            # add mets file as <mets:mptr>
                            metspointer = M.mptr({"LOCTYPE": "URL",
                                                  q(XLINK_NS, "title"): ("Mets file describing representation: %s of %s: urn:uuid:%s." % (rep_name, packagetype, packageid)),
                                                  q(XLINK_NS, "href"): rel_path_file,
                                                  "ID": "ID" + uuid.uuid4().__str__()})
                            #mets_structmap_rep_div.append(metspointer)
                            #mets_structmap_rep_div.append(M.fptr({"FILEID": id}))
                            physical_div.append(metspointer)    # IMPORTANT: The <mptr> element needs to be the first entry in a <div>, or the Mets will be invalid!
                            # also create a <fptr> for the Mets file
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            physical_div.append(M.fptr({"FILEID": id}))
                        elif filename and directory.endswith('schemas'):
                            # schema files
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            mets_structmap_schema_div.append(M.fptr({'FILEID': id}))
                            physical_div.append(M.fptr({'FILEID': id}))
                        elif filename:
                            id = self.addFile(os.path.join(directory, filename), mets_filegroup)
                            mets_structmap_content_div.append(M.fptr({'FILEID': id}))
                            physical_div.append(M.fptr({'FILEID': id}))

        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

        path_mets = os.path.join(self.root_path, 'METS.xml')
        with open(path_mets, 'w') as output_file:
            output_file.write(str)


class testMetsCreation(unittest.TestCase):
    def testCreateMets(self):
        metsgen = MetsGenerator(os.path.join("/var/data/earkweb/work/3b7f4c9e-a313-468a-a432-3506147d3829"))
        mets_data = {'packageid': '996ed635-3e13-4ee5-8e5b-e9661e1d9a93',
                     'type': 'AIP'}
        metsgen.createMets(mets_data)


if __name__ == '__main__':
    unittest.main()
