from lxml import etree, objectify
import os
import string
import uuid
from earkcore.metadata.XmlHelper import sequence_insert, q, XSI_NS
from earkcore.utils.datetimeutils import get_file_ctime_iso_date_str as iso_date
from earkcore.fixity.ChecksumFile import checksum
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm
from earkcore.filesystem import fsinfo

METS_NS = 'http://www.loc.gov/METS/'
XLINK_NS = 'http://www.w3.org/1999/xlink'
METS_NSMAP = {'mets': METS_NS, 'xlink': XLINK_NS}
M = objectify.ElementMaker(
    annotate=False,
    namespace=METS_NS,
    nsmap=METS_NSMAP)


class Mets:

    working_directory = '.'
    checksum_algorithm = ChecksumAlgorithm.SHA256

    def __init__(self, f=None, wd='./', alg=ChecksumAlgorithm.SHA256):
        """
        Constructor used to initialise METS from template or from empty METS object
        @type       f: string
        @param      f: Path to optional METS template file
        @type       wd: string
        @param      wd: Working directory (relative paths)
        @type       alg: earkcore.fixity.ChecksumAlgorithm
        @param      alg: Checksum algorighm
        """
        if f is None:
            self.root = M.mets(
                {q(XSI_NS, 'schemaLocation'): METS_NS + ' schemas/IP.xsd'},
                M.metsHdr,
                M.amdSec,
                M.fileSec,
                M.structMap(M.div)
            )
            self.add_agent('ARCHIVIST', 'ORGANIZATION', 'Institution')
        else:
            self.root = objectify.parse(f).getroot()
        self.working_directory = wd
        self.checksum_algorithm = alg

    @staticmethod
    def generate_id():
        return 'ID' + str(uuid.uuid4())

    @staticmethod
    def mets_find(root, path, arg, val):
        return root.find('{}[@{}="{}"]'.format(path, arg, val), METS_NSMAP)

    @staticmethod
    def xlink(file_path):
        return {'LOCTYPE': 'URL', q(XLINK_NS, 'href'): file_path, q(XLINK_NS, 'type'): 'simple'}

    def add_agent(self, role, agent_type, name):
        self.root.metsHdr.append(
            M.agent(
                {'ROLE': role, 'TYPE': agent_type},
                M.name(name)
            )
        )

    def add_dmd_sec(self, md_type, file_path):
        gen_id = self.generate_id()
        self.root.amdSec.addprevious(
            M.dmdSec(
                {'ID': gen_id},
                M.mdRef({'MDTYPE': md_type, 'CREATED': iso_date(file_path, wd=self.working_directory),
                 'CHECKSUM': checksum(file_path, wd=self.working_directory, alg=self.checksum_algorithm),
                 'CHECKSUMTYPE': ChecksumAlgorithm.str(self.checksum_algorithm), "SIZE": str(fsinfo.fsize(file_path, self.working_directory))}, self.xlink(file_path))
            )
        )
        return gen_id

    def __insert_into_amd_sec(self, md_node, successor_sections, md_type, file_path, adm_id):
        if adm_id == '':
            adm_id = self.generate_id()
        child = md_node(
            {'ID': adm_id},
            M.mdRef({'MDTYPE': md_type}, self.xlink(file_path))
        )
        sequence_insert(self.root.amdSec, child, successor_sections)
        return adm_id

    def add_tech_md(self, file_path, adm_id=''):
        successor_sections = ['rightsMD', 'sourceMD', 'digiprovMD']
        return self.__insert_into_amd_sec(M.techMD, successor_sections, 'PREMIS:OBJECT', file_path, adm_id)

    def add_rights_md(self, file_path, adm_id=''):
        successor_sections = ['sourceMD', 'digiprovMD']
        return self.__insert_into_amd_sec(M.rightsMD, successor_sections, 'PREMIS:RIGHTS', file_path, adm_id)

    def add_digiprov_md(self, file_path, adm_id=''):
        return self.__insert_into_amd_sec(M.digiprovMD, [], 'PREMIS:EVENT', file_path, adm_id)

    def find_amd_md(self, adm_id):
        return self.mets_find(self.root.amdSec, '*', 'ID', adm_id)

    @staticmethod
    def recursive_find(parent, tag, attribute, values):
        node = Mets.mets_find(parent, tag, attribute, values[0])
        if len(values) <= 1 or node is None:
            return node
        else:
            return Mets.recursive_find(node, tag, attribute, values[1:])

    def find_file_grp(self, grp_uses, parent=None):
        if parent is None:
            parent = self.root.fileSec
        return Mets.recursive_find(parent, 'mets:fileGrp', 'USE', grp_uses)

    def find_div(self, div_labels, parent=None):
        if parent is None:
            parent = self.root.structMap.div
        return Mets.recursive_find(parent, 'mets:div', 'LABEL', div_labels)

    def add_file_grp(self, grp_uses, file_grp_parent=None, div_parent=None):
        if file_grp_parent is None:
            file_grp_parent = self.root.fileSec
            div_parent = self.root.structMap.div
        file_grp = self.find_file_grp(grp_uses[:1], file_grp_parent)
        div = self.find_div(grp_uses[:1], div_parent)
        if file_grp is None:
            file_grp = M.fileGrp({'USE': grp_uses[0]})
            file_grp_parent.append(file_grp)
            div = M.div({'LABEL': grp_uses[0]})
            div_parent.append(div)
        if len(grp_uses) > 1:
            self.add_file_grp(grp_uses[1:], file_grp, div)

    def add_file(self, grp_uses, file_path, adm_ids):
        self.add_file_node(
            grp_uses,
            M.file(
                {'ID': self.generate_id(), 'ADMID': string.join(adm_ids), 'CREATED': iso_date(file_path, wd=self.working_directory),
                 'CHECKSUM': checksum(file_path, wd=self.working_directory, alg=self.checksum_algorithm),
                 'CHECKSUMTYPE': ChecksumAlgorithm.str(self.checksum_algorithm), "SIZE": str(fsinfo.fsize(file_path, self.working_directory))},
                M.FLocat(self.xlink(file_path))
            )
        )

    def add_file_node(self, grp_uses, file_node):
        self.add_file_grp(grp_uses)
        file_grp = self.find_file_grp(grp_uses)
        file_grp.append(file_node)
        div = self.find_div(grp_uses)
        div.append(
            M.fptr({'FILEID': file_node.get('ID')})
        )

    def copy_dmd_sec(self, aip_mets, filepath):
        md_ref = self.mets_find(aip_mets.root, 'mets:dmdSec/mets:mdRef', 'xlink:href', 'file://.' + filepath)
        self.add_dmd_sec(md_ref.get('MDTYPE'), md_ref.get(q(XLINK_NS, 'href')))

    @staticmethod
    def get_grp_uses(inner_file_grp):
        if inner_file_grp.tag != q(METS_NS, 'fileGrp'):
            return []
        else:
            grp_uses = Mets.get_grp_uses(inner_file_grp.getparent())
            grp_uses.append(inner_file_grp.get('USE'))
            return grp_uses

    def copy_file_info(self, aip_mets, filepath):
        f_locat = self.mets_find(aip_mets.root.fileSec, './/mets:file/mets:FLocat', 'xlink:href', 'file://.' + filepath)
        file_node = f_locat.getparent()
        self.add_file_node(Mets.get_grp_uses(file_node.getparent()), file_node)
        for adm_id in string.split(file_node.get('ADMID')):
            amd_md = aip_mets.find_amd_md(adm_id)
            if self.find_amd_md(adm_id) is None:
                if amd_md.tag == q(METS_NS, 'techMD'):
                    self.add_tech_md(amd_md.mdRef.get(q(XLINK_NS, 'href')), adm_id)
                elif amd_md.tag == q(METS_NS, 'rightsMD'):
                    self.add_rights_md(amd_md.mdRef.get(q(XLINK_NS, 'href')), adm_id)
                elif amd_md.tag == q(METS_NS, 'digiprovMD'):
                    self.add_digiprov_md(amd_md.mdRef.get(q(XLINK_NS, 'href')), adm_id)

    def validate(self):
        with open('../../Downloads/mets.xsd', 'r') as f:
            xmlschema = etree.XMLSchema(file=f)
        return xmlschema.validate(self.root)

    def __str__(self):
        return etree.tostring(self.root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

    def to_string(self):
        return self.__str__()



def main():
    with open('resources/METS_skeleton.xml', 'r') as mets_file:
        my_mets = Mets(wd='resources/workingdir', alg=ChecksumAlgorithm.SHA256)
    print my_mets.working_directory
    my_mets.add_dmd_sec('EAD', 'file://./metadata/EAD.xml')
    admids = []
    admids.append(my_mets.add_tech_md('file://./metadata/PREMIS.xml#Obj'))
    admids.append(my_mets.add_digiprov_md('file://./metadata/PREMIS.xml#Ingest'))
    admids.append(my_mets.add_rights_md('file://./metadata/PREMIS.xml#Right'))
    my_mets.add_file_grp(['submission'])
    my_mets.add_file(['submission'], 'file://./METS.xml', admids)
    my_mets.root.set('TYPE', 'AIP')
    print my_mets

    #print my_mets.validate()

if __name__ == "__main__":
    main()
