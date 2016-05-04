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

server_solr_query_url = "http://10.20.77.1:8983/solr/eark1/select?q={0}&wt=json"

server_repo_record_content_query = "http://10.20.77.1:12060/repository/table/eark1/record/{0}/field/n$content/data?ns.n=org.eu.eark"

server_hdfs_aip_query = "http://localhost:8081/hsink/fileresource/retrieve_newest?file={0}"

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

# Test settings

test_rest_endpoint_hdfs_upload = "http://81.189.135.189"
