import requests
import sys
import os
import os.path
import re

from eatb.storage.directorypairtreestorage import PairtreeStorage
from pairtree import PairtreeStorageClient

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from access.search.solrclient import SolrClient
from access.search.solrserver import SolrServer
from access.search.solrquery import SolrQuery

from config.configuration import solr_host, verify_certificate, solr_protocol
from config.configuration import solr_port
from config.configuration import config_path_storage


def index_aip_storage():
    solr_server = SolrServer(solr_protocol, solr_host, solr_port)
    print("Solr server base url: %s" % solr_server.get_base_url())
    sq = SolrQuery(solr_server)
    r = requests.get(sq.get_base_url(), verify=verify_certificate)
    if not r.status_code == 200:
        print("Solr server is not available at: %s" % sq.get_base_url())
        return
    else:
        print("Using Solr server at: %s" % sq.get_base_url())
    # delete index first
    r = requests.get(sq.get_base_url() + "storagecore1/update?stream.body=%3Cdelete%3E%3Cquery%3E*%3C/query%3E%3C/delete%3E&commit=true", verify=verify_certificate)
    package_count = 0
    solr_client = SolrClient(solr_server, "storagecore1")
    for dirpath,_,filenames in os.walk(config_path_storage):
       for f in filenames:
           package_abs_path = os.path.abspath(os.path.join(dirpath, f))
           if package_abs_path.endswith(".tar"):
               print("=========================================================")
               print(package_abs_path)
               print("=========================================================")
               _, file_name = os.path.split(package_abs_path)

               id_path = package_abs_path[0:re.search('data\/v[0-9]{5,5}\/', package_abs_path).start()]

               store = PairtreeStorageClient(store_dir=config_path_storage, uri_base='http')
               dpts = PairtreeStorage(config_path_storage)
               identifier = store._get_id_from_dirpath(id_path)
               given_package_version = re.search(r'v[0-9]{5,5}', package_abs_path).group(0)
               current_version = dpts.curr_version(identifier)
               if given_package_version == current_version:
                   current_version_num = dpts.curr_version_num(identifier)
                   results = solr_client.post_tar_file(package_abs_path, identifier, current_version_num)
                   print("Total number of files posted: %d" % len(results))
                   num_ok = sum(1 for result in results if result['status'] == 200)
                   print("Number of files posted successfully: %d" % num_ok)
                   num_failed = sum(1 for result in results if result['status'] != 200)
                   print("Number of plain documents: %d" % num_failed)
                   package_count += 1
    print("Indexing of %d packages available in local storage finished" % package_count)


if __name__ == '__main__':
    index_aip_storage()
