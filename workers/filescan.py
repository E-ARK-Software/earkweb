__author__ = 'jan'

import os
from earkcore.metadata.mets.MetsManipulate import Mets
from earkcore.metadata.premis.PremisManipulate import Premis
from earkcore.metadata.identification import MetaIdentification
from config.config import root_dir
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm


def filescan(path, mets, premis):
    '''
    This function scans a directory for every file inside,
    and adds it to the submission METS/PREMIS.
    '''

    # Add METS file groups
    mets.add_file_grp(['submission'])
    mets.add_file_grp(['schemas'])
    mets.add_file_grp(['customMD'])

    # path length
    # TODO: retrieve from somewhere
    workdir_length = len('/var/data/earkweb/work/9990974d-2027-467d-beb4-9c4137ab6c38/DNA_AVID.SA.18001.01_141104')

    # Known metadata formats.
    # TODO: expand so we have tag + metadata section
    md_type_list = {'ead': 'techMD',
                    'eac-cpf': 'dmdSec',
                    'premis': 'techMD'}

    # TODO: add PREMIS
    # TODO: use the md_type_list, check if xml_tag is known (case sensitive?):
    # TODO: if yes, the correct section is also known; if no, list as customMD
    for directory, subdirectory, filenames in os.walk(path):
        for filename in filenames:
            rel_path_file = 'file://.' + directory[workdir_length:] + '/' + filename
            if directory[-8:].lower() == 'metadata':
                xml_tag = MetaIdentification.MetaIdentification(os.path.join(directory, filename))
                if xml_tag == 'schema':
                    mets.add_file(['schemas'], rel_path_file, '')
                elif xml_tag in md_type_list:
                    if md_type_list[xml_tag] == 'techMD':
                        mets.add_tech_md(rel_path_file, '')
                    elif md_type_list[xml_tag] == 'dmdSec':
                        mets.add_dmd_sec(xml_tag, rel_path_file)
                #elif xml_tag == 'eac-cpf':
                #    mets.add_dmd_sec(xml_tag, rel_path_file)
                #elif xml_tag == 'premis':
                #    mets.add_tech_md(rel_path_file, '')
                #elif xml_tag == 'ead':
                #    mets.add_dmd_sec(xml_tag, rel_path_file)
                elif xml_tag:
                    mets.add_file(['customMD'], rel_path_file, 'admids')
            else:
                # Everything in other folders is content.
                mets.add_file(['submission'], rel_path_file, 'admids')

    # TODO: create file
    print mets


def main():
    ip_work_dir = '/var/data/earkweb/work/9990974d-2027-467d-beb4-9c4137ab6c38/DNA_AVID.SA.18001.01_141104'

    # create submission METS
    mets_skeleton_file = root_dir + '/earkresources/METS_skeleton.xml'
    with open(mets_skeleton_file, 'r') as mets_file:
        submission_mets_file = Mets(wd=ip_work_dir, alg=ChecksumAlgorithm.SHA256)

    # scan package, update METS and PREMIS
    filescan('/var/data/earkweb/work/9990974d-2027-467d-beb4-9c4137ab6c38/DNA_AVID.SA.18001.01_141104',
             submission_mets_file, 'premis')


if __name__ == '__main__':
    main()