import logging
import requests
import json
import os
from access.search.solrclient import SolrClient
from access.search.solrquery import SolrQuery
from access.search.solrserver import SolrServer
from config.configuration import verify_certificate, solr_protocol

logger = logging.getLogger(__name__)


def index_repository():
    from config.configuration import solr_host
    from config.configuration import solr_port
    from config.configuration import config_path_storage

    solr_server = SolrServer(solr_protocol, solr_host, solr_port)
    logger.info("Solr server base url: %s" % solr_server.get_base_url())
    sq = SolrQuery(solr_server)
    r = requests.get(sq.get_base_url(), verify=verify_certificate)
    if not r.status_code == 200:
        logger.error("Solr server is not available at: %s" % sq.get_base_url())
        return
    else:
        logger.info("Using Solr server at: %s" % sq.get_base_url())
    # delete index first
    url_part = "storagecore1/update?stream.body=%3Cdelete%3E%3Cquery%3E*%3C/query%3E%3C/delete%3E&commit=true"
    requests.get(sq.get_base_url() + url_part, verify=verify_certificate)
    package_count = 0
    solr_client = SolrClient(solr_server, "storagecore1")
    for dirpath, _, filenames in os.walk(config_path_storage):
        for f in filenames:
            package_abs_path = os.path.abspath(os.path.join(dirpath, f))
            if package_abs_path.endswith(".tar"):
                logger.info("=========================================================")
                logger.info(package_abs_path)
                logger.info("=========================================================")
                _, file_name = os.path.split(package_abs_path)
                identifier = file_name[0:-4]
                results = solr_client.post_tar_file(package_abs_path, identifier, version=1)
                logger.info("Total number of files posted: %d" % len(results))
                num_ok = sum(1 for result in results if result['status'] == 200)
                logger.info("Number of files posted successfully: %d" % num_ok)
                num_failed = sum(1 for result in results if result['status'] != 200)
                logger.info("Number of plain documents: %d" % num_failed)
                package_count += 1
    logger.info("Indexing of %d packages available in local storage finished" % package_count)


class SolrUtility(object):
    """
    SolrUtility offers functions to access a Solr instance.
    """

    def __init__(self):
        """
        Initialise class.
        @return:
        """
        self.solr_unique_key = None
        self.solr_instance = None

    def availability(self, solr_base_url, solr_unique_key):
        """
        Call this method with a Solr url and the unique key as arguments. If the Solr instance is reachable, they are
        set as class variables and 200 is returned. If not, variables remain 'None' and the status code is returned.
        @param solr_base_url: base URL of solr instance to be used: http://<ip>:<port>/solr/<core>/
        @param solr_unique_key: key that is used as unique identifier within the Solr index (e.g. 'id', 'lily.key')
        @return:
        """
        # add 'admin/ping' to URL to check if Solr is reachable
        url = os.path.join(solr_base_url, 'admin/ping/')
        solr_status = requests.get(url, verify=verify_certificate).status_code
        if solr_status == 200:
            self.solr_unique_key = solr_unique_key
            self.solr_instance = solr_base_url
            print('Solr instance %s reachable.' % solr_base_url)
            return solr_status
        else:
            print('GET request to %s/admin/ping returned HTML status: %d.' % (solr_base_url, solr_status))
            return solr_status

    def send_query(self, query_string):
        """
        Send query to Solr, return result.
        @return:
        """
        url_suffix = 'select?wt=json&q='   # q=*:*
        query_url = os.path.join(self.solr_instance, url_suffix)
        query = requests.get(query_url + query_string, verify=verify_certificate)
        if query.status_code == 200:
            return query.json()['response']['docs']
        else:
            # return query.status_code
            return False

    def set_field(self, record_identifier, field, content):
        """
        Update a field with new content. Substitutes previous content.
        @param record_identifier:
        @param field:
        @param content:
        @return:
        """
        url_suffix = 'update'
        update_url = os.path.join(self.solr_instance, url_suffix)
        update_headers = {'Content-Type': 'application/json'}
        update_data = json.dumps([{field: {'set': content}, self.solr_unique_key: record_identifier}])
        update = requests.post(update_url, data=update_data, headers=update_headers, verify=verify_certificate)
        print(update.text)
        return update.status_code

    def set_multiple_fields(self, record_identifier, kv_tuple_list):
        """
        Update a solr document given a list of fieldname/value pairs
        example: set_multiple_fields("bd74c030-3161-4962-9f98-47f6d00c89cc",
            [("field1_s", "value1"), ("field2_b", "true")])
        @param record_identifier: record identifier (solr identifier)
        @param kv_tuple_list: list of fieldname/value pairs
        @return: status code
        """
        url_suffix = 'update'
        update_url = os.path.join(self.solr_instance, url_suffix)
        update_headers = {'Content-Type': 'application/json'}
        update_data = dict()
        update_data[self.solr_unique_key] = record_identifier
        for kv_tuple in kv_tuple_list:
            update_data[kv_tuple[0]] = {'set': kv_tuple[1]}
        update_doc = json.dumps([update_data])
        update = requests.post(update_url, data=update_doc, headers=update_headers, verify=verify_certificate)
        print(update.text)
        return update.status_code

    def update_document(self, record_identifier, kv_pairs):
        """
        Update a solr document given a list of fieldname/value pairs
        example: update_document("bd74c030-3161-4962-9f98-47f6d00c89cc",
            [{"field_value": "value1", "field_name": "field1_s"}, {"field_value": "value2", "field_name": "field2_s"}])
        @param record_identifier: record identifier (solr identifier)
        @param kv_pairs: list of fieldname/value pairs
        @return: status code
        """
        url_suffix = 'update'
        update_url = os.path.join(self.solr_instance, url_suffix)
        update_headers = {'Content-Type': 'application/json'}
        update_data = dict()
        update_data[self.solr_unique_key] = record_identifier
        for kv_pair in kv_pairs:
            update_data[kv_pair['field_name']] = {'set': kv_pair['field_value']}
        update_doc = json.dumps([update_data])
        update = requests.post(update_url, data=update_doc, headers=update_headers, verify=verify_certificate)

        print(update_url)
        print(json.dumps([update_data], indent=4))
        return update.status_code

    def get_doc_id_from_path(self, safe_urn_identifier, entry_path):
        """
        Get identifier from solr document
        @param safe_urn_identifier: safe identifier, e.g. urn:uuid:0426f626-d51d-449c-84fa-d5c32d728509
        @param entry_path: entry path, e.g. /submission/representations/rep1/data/Example1.docx
        @return: document identifier, e.g. "d66c0d7b-0b9d-4a4f-a1d5-7d829f109018"
        """
        solr_query = 'path:"%s%s"' % (safe_urn_identifier, entry_path)
        query_result = self.send_query(solr_query)
        if query_result is False:
            raise RuntimeError("No query result")
        try:
            identifier = query_result[0][self.solr_unique_key]
        except KeyError as e:
            raise RuntimeError("Unable to get document identifier: %s" % e)

        # if "lily.key" in query_result[0]:
        #     identifier = query_result[0]['lily.key']
        # else:
        #     identifier = query_result[0]['id']
        # if not identifier:
        #     raise RuntimeError("Unable to get document identifier")
        return identifier

    # def add_to_field(self, record_identifier, field, content):
    #     """
    #     Add a new entry to a field. Existing field needs to be a multi-valued string field (a list).
    #     @param record_identifier:
    #     @param field:
    #     @param content:
    #     @return:
    #     """
    #     # field needs to be multi-valued string (adding to a list)
    #     url_suffix = 'update'
    #     add_url = self.solr_instance + url_suffix
    #     update_headers = {'Content-Type': 'application/json'}
    #     update_data = json.dumps([{field: {'add': content}, self.solr_unique_key: record_identifier}])
    #     update = requests.post(add_url, data=update_data, headers=update_headers, verify=verify_certificate)
    #     return update.status_code

    # def remove_from_field(self):
    #     # remove from a field (which needs to be a list)
    #     pass
