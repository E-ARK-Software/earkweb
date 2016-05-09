import os
import string
import socket

devHostnames = ['pluto', 'Vulcan']

# earkweb django server
django_service_ip = "127.0.0.1" if socket.gethostname() in devHostnames else "10.20.77.1" if socket.gethostname() == "hadoop-1" else "81.189.135.189"
django_service_port = 8000

# mysql server
mysql_server_ip = "172.17.0.2" if (socket.gethostname() != "hadoop-1" and socket.gethostname() != "earkdev" and socket.gethostname() not in devHostnames) else "127.0.0.1"

# access solr server
access_solr_server_ip = "81.189.135.189"
access_solr_port = 8983
access_solr_core = "eark1"

# storage solr server
local_solr_server_ip = "172.17.0.2"
local_solr_port = 8983
local_solr_core = "earkstorage"

# lily content access
lily_content_access_ip = "81.189.135.189"
lily_content_access_port = 12060
lily_content_access_core = "eark1"

# hdfs upload service
hdfs_upload_service_ip = "81.189.135.189"
hdfs_upload_service_port = 8081

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

server_repo_record_content_query = "http://%s:%d/repository/table/%s/record/{0}/field/n$content/data?ns.n=org.eu.eark" % (lily_content_access_ip, lily_content_access_port, lily_content_access_core)

server_hdfs_aip_query = "http://%s:%d/hsink/fileresource/retrieve_newest?file={0}" % (hdfs_upload_service_ip, hdfs_upload_service_port)

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

test_rest_endpoint_hdfs_upload = "http://%s" % hdfs_upload_service_ip
