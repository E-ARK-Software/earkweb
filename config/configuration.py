import os
import string
import ConfigParser

import logging
logger = logging.getLogger(__name__)

root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
earkweb_version = '0.3.3.'

config = ConfigParser.RawConfigParser()
config.read(os.path.join(root_dir, 'config/settings.cfg'))

# earkweb django server
django_service_ip = config.get('server', 'django_service_ip')
django_service_port = config.getint('server', 'django_service_port')

redis_ip = config.get('server', 'redis_ip')
redis_port = config.getint('server', 'redis_port')

# rabbitmq server
rabbitmq_ip = config.get('server', 'rabbitmq_ip')
rabbitmq_port = config.getint('server', 'rabbitmq_port')
rabbitmq_user = config.get('server', 'rabbitmq_user')
rabbitmq_password = config.get('server', 'rabbitmq_password')

# mysql server
mysql_server_ip = config.get('server', 'mysql_server_ip')
mysql_port = config.getint('server', 'mysql_port')
mysql_user = config.get('server', 'mysql_user')
mysql_password = config.get('server', 'mysql_password')
mysql_earkweb_db = config.get('server', 'mysql_earkweb_db')
mysql_celerybackend_db = config.get('server', 'mysql_celerybackend_db')

logger.info("mysql_server_ip: %s" % mysql_server_ip)

# access solr server
access_solr_server_ip = config.get('server', 'access_solr_server_ip')
access_solr_port = config.getint('server', 'access_solr_port')
access_solr_core = config.get('server', 'access_solr_core')

# storage solr server
local_solr_server_ip = config.get('server', 'storage_solr_server_ip')
local_solr_port = config.getint('server', 'storage_solr_port')
local_solr_core = config.get('server', 'storage_solr_core')

# lily content access
lily_content_access_ip = config.get('server', 'lily_content_access_ip')
lily_content_access_port = config.getint('server', 'lily_content_access_port')
lily_content_access_core = config.get('server', 'lily_content_access_core')

# hdfs upload service
hdfs_upload_service_ip = config.get('server', 'hdfs_upload_service_ip')
hdfs_upload_service_port = config.getint('server', 'hdfs_upload_service_port')
hdfs_upload_service_endpoint_path = config.get('server', 'hdfs_upload_service_endpoint_path')
hdfs_upload_service_resource_path = config.get('server', 'hdfs_upload_service_resource_path')

mets_schema_file = os.path.join(root_dir, config.get('schemas', 'mets_schema_file'))
premis_schema_file = os.path.join(root_dir, config.get('schemas', 'premis_schema_file'))

# size limit for direct file display
config_max_filesize_viewer = config.getint('limits', 'config_max_filesize_viewer')

config_path_reception = config.get('paths', 'config_path_reception')
config_path_work = config.get('paths', 'config_path_work')
config_path_storage = config.get('paths', 'config_path_storage')
config_path_access = config.get('paths', 'config_path_access')

# EAD metadata file pattern
metadata_file_pattern_ead =  config.get('metadata', 'metadata_file_pattern_ead')

# location of METS Template
template_METS_path = root_dir + '/lib/metadata/mets/template_METS.xml'

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

# NLP settings
stanford_jar = config.get('nlp', 'stanford_jar_path')
stanford_ner_models = config.get('nlp', 'stanford_models_path')
text_category_models = config.get('nlp', 'category_models_path')
config_path_nlp = config.get('nlp', 'config_path_nlp')

# Solr fields
# {'name': '', 'type': '', 'stored': ''}
# {'name': '', 'type': '', 'stored': '', 'indexed': 'true'}
solr_field_list = [{'name': 'package', 'type': 'string', 'stored': 'true'},
                   {'name': 'path', 'type': 'string', 'stored': 'true'},
                   {'name': 'size', 'type': 'long', 'stored': 'true'},
                   {'name': 'confidential', 'type': 'boolean', 'stored': 'true'},
                   {'name': 'textCategory', 'type': 'text_general', 'stored': 'true'},
                   {'name': 'content', 'type': 'text_general', 'stored': 'true', 'indexed': 'true'},
                   {'name': 'contentType', 'type': 'string', 'stored': 'true'}]
solr_copy_fields = [{'source': '_text_', 'dest': 'content'}, {'source': 'content_type', 'dest': 'contentType'}]
