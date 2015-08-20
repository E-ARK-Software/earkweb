import os
from earkcore.metadata.mets import MetsManipulate

WORKING_DIRECTORY = './working_area'
METADATA_DIRECTORY = 'aip-metadata'


def convert(directory_name):
    print 'starting DIP conversion'
    rootdir = os.path.join(WORKING_DIRECTORY, directory_name)
    dip_mets = MetsManipulate.Mets()
    dip_mets.root.set('TYPE', 'DIP')
    with open(os.path.join(rootdir, 'METS.xml'), 'r') as f:
        aip_mets = MetsManipulate.Mets(f)
    for subdir, dirs, files in os.walk(rootdir):
        rel_subdir = subdir[len(rootdir):]
        if subdir == os.path.join(rootdir, METADATA_DIRECTORY):
            for f in files:
                if f != 'PREMIS.xml':
                    filepath = os.path.join(rel_subdir, f)
                    dip_mets.copy_dmd_sec(aip_mets, filepath)
        else:
            for f in files:
                if f != 'METS.xml':
                    filepath = os.path.join(rel_subdir, f)
                    dip_mets.copy_file_info(aip_mets, filepath)
    print dip_mets


def main():
    convert('DIP1')

if __name__ == "__main__":
    main()
