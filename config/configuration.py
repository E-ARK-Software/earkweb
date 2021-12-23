#!/usr/bin/env python
# coding=UTF-8
import sys
import os

from util import build_url

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # noqa: E402
import string
import configparser

import logging
logger = logging.getLogger(__name__)

root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

# ATTENTION: Environment variables overrule config file settings in settings/settings.cfg
# configuration file
config = configparser.ConfigParser()
config['DEFAULT'] = {}
config.sections()
config.read(os.path.join(root_dir, 'settings/settings.cfg'))

# ignore certificate verification failures
verify_certificate = False

fido_enabled = False

# version
sw_version = config.get('repo', 'sw_version')
sw_version_date = config.get('repo', 'sw_version_date')
app_label = config.get('repo', 'app_label')
default_org = config.get('repo', 'default_org')
is_test_instance = config.getboolean('repo', 'is_test_instance')

backend_api_key = config.get('system', "backend_api_key")

# repository
logo = config.get('repo', 'logo')
repo_identifier = config.get('repo', 'repo_identifier')
repo_title = config.get('repo', 'repo_title')
repo_description = config.get('repo', 'repo_description')
repo_catalogue_issued = config.get('repo', 'repo_catalogue_issued')
repo_catalogue_modified = config.get('repo', 'repo_catalogue_modified')

_conf_repr_dir = config.get('repo', 'representations_directory')
representations_directory = _conf_repr_dir if _conf_repr_dir else "representations"
metadata_directory = _conf_repr_dir if _conf_repr_dir else "metadata"
node_namespace_id = config.get('repo', 'node_namespace_id')

# logfiles
logfile_ui = config.get('logs', 'logfile_ui')
logfile_request = config.get('logs', 'logfile_request')
logfile_celery = config.get('logs', 'logfile_celery')
logfile_celery_proc = config.get('logs', 'logfile_celery_proc')

# repo
django_debug = config.get('server', 'django_debug')
django_secret_key = config.get('server', 'django_secret_key')
django_service_protocol = config.get('server', 'django_service_protocol')
django_service_host = config.get('server', 'django_service_host')
django_service_port = int(config.get('server', 'django_service_port'))
django_service_url = build_url(django_service_protocol, django_service_host, django_service_port, app_label)
package_access_url_pattern = \
    "%s://%s%s/%s/access/package/$packageid/" % \
    (django_service_protocol, django_service_host,
     "" if django_service_port == 80 else ":%s" % django_service_port, app_label)
package_download_url_pattern = "%s$dataassetid/" % package_access_url_pattern

# backend
django_backend_service_protocol = config.get('server', 'django_backend_service_protocol')
django_backend_service_host = config.get('server', 'django_backend_service_host')
django_backend_service_port = config.get('server', 'django_backend_service_port')
django_backend_service_url = build_url(django_backend_service_protocol, django_backend_service_host, django_backend_service_port, app_label)
django_backend_service_api_url = "%s/api" % django_backend_service_url

# mysql server
mysql_host = config.get('server', 'mysql_host')
mysql_port = config.getint('server', 'mysql_port')
mysql_user = config.get('server', 'mysql_user')
mysql_password = config.get('server', 'mysql_password')
mysql_db = default = config.get('server', 'mysql_db')

# redis
redis_host = config.get('server', 'redis_host')
redis_port = int(config.get('server', 'redis_port'))
redis_password = config.get('server', 'redis_password')

# rabbitmq
rabbitmq_host = config.get('server', 'rabbitmq_host')
rabbitmq_port = int(config.get('server', 'rabbitmq_port'))
rabbitmq_user = config.get('server', 'rabbitmq_user')
rabbitmq_password = config.get('server', 'rabbitmq_password')

# solr
solr_protocol = config.get('server', 'solr_protocol')
solr_host = config.get('server', 'solr_host')
solr_port = int(config.get('server', 'solr_port'))
solr_core = config.get('server', 'solr_core')
solr_service_url = build_url(solr_protocol, solr_host, solr_port, "solr")
solr_core_url = '%s/%s' % (solr_service_url, solr_core)
solr_core_ping_url = '%s/admin/ping' % solr_core_url
solr_core_overview_url = '%s/#/%s/core-overview' % (solr_service_url, solr_core)

# flower
flower_protocol = config.get('server', 'flower_protocol')
flower_host = config.get('server', 'flower_host')
flower_port = int(config.get('server', 'flower_port'))
flower_path = config.get('server', 'flower_path')
flower_service_url = '%s://%s:%s%s' % (flower_protocol, flower_host, flower_port, flower_path)

# repo data directories
config_path_reception = config.get('paths', 'config_path_reception')
config_path_work = config.get('paths', 'config_path_work')
config_path_storage = config.get('paths', 'config_path_storage')
config_path_access = config.get('paths', 'config_path_access')

# EAD metadata file pattern
metadata_file_pattern_ead =  config.get('metadata', 'metadata_file_pattern_ead')

# maximum number of submissions by web client
max_submissions_web_client = 50

# size limit for direct file display
file_size_limit = config.getint('limits', 'config_max_filesize_viewer')
config_max_http_download = config.getint('limits', 'config_max_http_download')

dip_download_base_url = config.get('access', 'dip_download_base_url')
dip_download_path = config.get('access', 'dip_download_path')

commands = {
    'gpg_passphrase_encrypt_file':
        ["gpg", "--yes", "--batch", "--passphrase", string.Template("$passphrase"), "-c", string.Template("$file")],
    'gpg_passphrase_decrypt_file':
        ["gpg", "--yes", "--batch", "--passphrase", string.Template("$passphrase"), "--output", string.Template("$decrypted_file"), "-d", string.Template("$encrypted_file")],
    'summain':
        ["/usr/bin/summain", "-f", "json", "-c", "SHA256", "--exclude=Ino,Dev,Uid,Username,Gid,Group,Nlink,Mode",
         "--output", string.Template("$manifest_file"), string.Template("$package_dir")],
    'summainstdout':
        ["/usr/bin/summain", "-f", "json", "-c", "SHA256", "--exclude=Ino,Dev,Uid,Username,Gid,Group,Nlink,Mode", string.Template("$package_dir")],
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

# Solr fields
# {'name': '', 'type': '', 'stored': ''}
# {'name': '', 'type': '', 'stored': '', 'indexed': 'true'}
solr_field_list = [{'name': 'packagetype', 'type': 'string', 'stored': 'true'},
                   {'name': 'package', 'type': 'string', 'stored': 'true'},
                   {'name': 'path', 'type': 'string', 'stored': 'true'},
                   {'name': 'size', 'type': 'plong', 'stored': 'true'},
                   {'name': 'indexdate', 'type': 'pdate', 'stored': 'true'},
                   {'name': 'archivedate', 'type': 'pdate', 'stored': 'true'},
                   {'name': 'is_metadata', 'type': 'boolean', 'stored': 'false', 'indexed': 'true'},
                   {'name': 'is_content_data', 'type': 'boolean', 'stored': 'false', 'indexed': 'true'},
                   {'name': 'confidential', 'type': 'boolean', 'stored': 'true'},
                   {'name': 'textCategory', 'type': 'text_general', 'stored': 'true'},
                   {'name': 'content', 'type': 'text_general', 'stored': 'true', 'indexed': 'true'},
                   {'name': 'contentType', 'type': 'strings', 'stored': 'true'},
                   {'name': 'content_type', 'type': 'strings', 'stored': 'true', 'indexed': 'true'}]
solr_copy_fields = [{'source': 'content_type', 'dest': 'contentType'}]

# Solr config
# {'type':'', 'path': '', 'class': '', 'field_name':'', 'field_value': ''}
solr_config_changes = [{'type': 'update-requesthandler', 'path': '/update/extract', 'class': 'solr.extraction.ExtractingRequestHandler',
                        'fields': {'fmap.content': 'content', 'lowernames': 'true', 'fmap.meta': 'ignored'}}]


flower_host = config.get('server', 'flower_host')
flower_port = int(config.get('server', 'flower_port'))
flower_path = config.get('server', 'flower_path')

def log_current_configuration():
    logger.info("Web-UI: %s://%s:%s" % (django_service_protocol, django_service_host, django_service_port))
    logger.info("MySQL: mysql://%s@%s:%d/%s" % (mysql_user, mysql_host, mysql_port, mysql_db))
    logger.info("Redis: redis://:%s@%s:%d/0" % (redis_password, redis_host, redis_port))
    logger.info("RabbitMQ: amqp://%s:%s@%s:%d/" % (rabbitmq_user, rabbitmq_password, rabbitmq_host, rabbitmq_port))
    logger.info("SolR: %s://%s:%d/solr/#/%s" % (solr_protocol, solr_host, solr_port, solr_core))
    logger.info("Flower: %s" % flower_service_url)

