import os
from earkcore.metadata.mets import MetsManipulate

WORKING_DIRECTORY = './working_area'
METADATA_DIRECTORY = 'aip-metadata'

def convert(directory_name):
    print 'starting DIP conversion'
    rootdir = os.path.join(WORKING_DIRECTORY, directory_name)
    dip_mets = MetsManipulate.Mets()
    with open(os.path.join(rootdir, 'METS.xml'), 'r') as f:
        aip_mets = MetsManipulate.Mets(f)
    for subdir, dirs, files in os.walk(rootdir):
        rel_subdir = subdir[len(rootdir):]
        if subdir != rootdir and subdir != os.path.join(rootdir, METADATA_DIRECTORY):
            for file in files:
                if file != 'METS.xml':
                    filepath = os.path.join(rel_subdir, file)
                    dip_mets.copy_file_info(aip_mets, filepath)
    print dip_mets
    print dip_mets.validate()

convert('DIP1')
