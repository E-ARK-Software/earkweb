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

    md_type_list = ['ead', 'eac', 'premis', 'mets']

    # TODO: add PREMIS
    for directory, subdirectory, filenames in os.walk(path):
        for filename in filenames:
            if directory[-8:].lower() == 'metadata':
                 if filename[-3:] == 'xsd':
                    mets.add_file(['schemas'], rel_path_file, '')
                 elif filename[-3:] == 'xml':
                    if (filename[:3].lower() == 'ead' or filename[-7:].lower() == 'ead.xml'):
                        mets.add_dmd_sec('ead', rel_path_file)
                    elif (filename[:3].lower() == 'eac' or filename[-7:].lower() == 'eac.xml'):
                        mets.add_dmd_sec('eac', rel_path_file)
                    elif (filename[:6].lower() == 'premis' or filename[-10:].lower() == 'premis.xml'):
                        mets.add_tech_md(rel_path_file, '')
                    elif filename:
                        xml_tag = MetaIdentification.MetaIdentification(directory + '/' + filename)
                        if xml_tag.lower() in md_type_list:
                            # TODO see rules above, and add accordingly
                            mets.add_tech_md(rel_path_file, '')
                        elif xml_tag.lower() not in md_type_list:
                            # custom metadata format?
                            mets.add_file(['customMD'], rel_path_file, 'admids')
            else:
                # Everything in other folders is content.
                rel_path_file = 'file://.' + directory[workdir_length:] + '/' + filename
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