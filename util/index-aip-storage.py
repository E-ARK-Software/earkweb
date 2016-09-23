__author__ = "Jan Rörden, Roman Karl, Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

import requests
import sys
import os
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from earkcore.search.solrclient import SolrClient
from earkcore.search.solrserver import SolrServer
from earkcore.search.solrquery import SolrQuery

from config.configuration import local_solr_server_ip
from config.configuration import local_solr_port
from config.configuration import config_path_storage

def index_aip_storage():
    solr_server = SolrServer(local_solr_server_ip, local_solr_port)
    print "Solr server base url: %s" % solr_server.get_base_url()
    sq = SolrQuery(solr_server)
    r = requests.get(sq.get_base_url())
    if not r.status_code == 200:
        print "Solr server is not available at: %s" % sq.get_base_url()
        return
    else:
        print "Using Solr server at: %s" % sq.get_base_url()
    # delete index first
    r = requests.get(sq.get_base_url() + "earkstorage/update?stream.body=%3Cdelete%3E%3Cquery%3E*%3C/query%3E%3C/delete%3E&commit=true")
    package_count = 0
    solr_client = SolrClient(solr_server, "earkstorage")
    for dirpath,_,filenames in os.walk(config_path_storage):
       for f in filenames:
           package_abs_path = os.path.abspath(os.path.join(dirpath, f))
           if package_abs_path.endswith(".tar"):
               print "========================================================="
               print package_abs_path
               print "========================================================="
               _, file_name = os.path.split(package_abs_path)
               identifier = file_name[0:-4]
               results = solr_client.post_tar_file(package_abs_path, identifier)
               print "Total number of files posted: %d" % len(results)
               num_ok = sum(1 for result in results if result['status'] == 200)
               print "Number of files posted successfully: %d" % num_ok
               num_failed = sum(1 for result in results if result['status'] != 200)
               print "Number of plain documents: %d" % num_failed
               package_count += 1
    print "Indexing of %d packages available in local storage finished" % package_count


if __name__ == '__main__':
    index_aip_storage()
