import os
import string


root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
mets_schema_file = os.path.join(root_dir, 'earkresources/schemas/mets_1_11.xsd')
premis_schema_file = os.path.join(root_dir, 'earkresources/schemas/premis-v2-2.xsd')

# size limit for direct file display
config_max_filesize_viewer = 4194304

# location of METS Template
template_METS_path = root_dir + '/lib/metadata/mets/template_METS.xml'

config_path_reception = "/var/data/earkweb/reception"
config_path_ingest = "/var/data/earkweb/ingest"
config_path_work = "/var/data/earkweb/work"
config_path_storage = "/var/data/earkweb/storage"
config_path_access = "/var/data/earkweb/access"

commands = {
    'summain':
        ["/usr/bin/summain", "-c", "SHA256", "-c", "MD5", "--exclude=Ino,Dev,Uid,Username,Gid,Group,Nlink,Mode",
         "--output", string.Template("$manifest_file"), string.Template("$package_dir")],
    'untar':
        ["tar", "-xf", string.Template("$tar_file"), "-C", string.Template("$target_dir")],
    'pdftohtml':
        ["pdftohtml", "-c", "-s", "-noframes", string.Template("$pdf_file"), string.Template("$html_file")],
    'pdftopdfa':
        ['gs', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dUseCIEColor', '-sProcessColorModel=DeviceCMYK', '-sDEVICE=pdfwrite',
         '-sPDFACompatibilityPolicy=1', string.Template('$output_file'), string.Template('$input_file')],
    'totiff':
        ['convert', string.Template('$input_file'), string.Template('$output_file')],
    'blank':
        [string.Template('$command')]
}
