import os
root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

# list of root-level folders in the AIP
aip_folders = (
    'aip-metadata',
    'representations',
    'schemas',
)

# location of METS Template
template_METS_path = root_dir+'/lib/metadata/mets/template_METS.xml'