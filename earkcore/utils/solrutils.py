import requests
import sys
import json
from config.configuration import access_solr_core, access_solr_port, access_solr_server_ip
from config.configuration import local_solr_core, local_solr_port, local_solr_server_ip


class SolrUtility(object):
    """
    SolrUtility offers functions to access a Solr instance.
    """

    def __init__(self):
        """
        Initialise class, check Solr availability.
        @return:
        """
        local_solr = 'http://%s:%s/solr/%s/' % (local_solr_server_ip, local_solr_port, local_solr_core)
        access_solr = 'http://%s:%s/solr/%s/' % (access_solr_server_ip, access_solr_port, access_solr_core)

        # field used as unique identifier
        self.solr_unique_key = 'id'

        # add 'admin/ping' to URL to check if Solr is reachable
        if requests.get(local_solr + 'admin/ping').status_code == 200:
            self.solr_instance = local_solr
            print 'Using local Solr instance.'
        elif requests.get(access_solr + 'adming/ping').status_code == 200:
            self.solr_instance = access_solr
            self.solr_unique_key = 'lily.key'
            print 'Using distributed Solr instance.'
        else:
            sys.exit('No Solr instance reachable.')

    def send_query(self, query_string):
        """
        Send query to Solr, return result.
        @return:
        """
        url_suffix = 'select?wt=json&q='   # q=*:*
        query_url = self.solr_instance + url_suffix
        query = requests.get(query_url + query_string)
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
        update_url = self.solr_instance + url_suffix
        update_headers = {'Content-Type': 'application/json'}
        update_data = json.dumps([{field: {'set': content}, self.solr_unique_key: record_identifier}])
        print update_data
        update = requests.post(update_url, data=update_data, headers=update_headers)
        print update.text
        return update.status_code

    def set_multiple_fields(self, record_identifier, kv_tuple_list):
        """
        Update a solr document given a list of fieldname/value pairs
        example: set_multiple_fields("bd74c030-3161-4962-9f98-47f6d00c89cc", [("field1_s", "value1"), ("field2_b", "true")])
        @param record_identifier: record identifier (solr identifier)
        @param kv_tuple_list: list of fieldname/value pairs
        @return: status code
        """
        url_suffix = 'update'
        update_url = self.solr_instance + url_suffix
        update_headers = {'Content-Type': 'application/json'}
        update_data = dict()
        update_data[self.solr_unique_key] = record_identifier
        for kv_tuple in kv_tuple_list:
            update_data[kv_tuple[0]] = {'set': kv_tuple[1]}
        update_doc = json.dumps([update_data])
        update = requests.post(update_url, data=update_doc, headers=update_headers)
        return update.text

    def update_document(self, record_identifier, kv_pairs):
        """
        Update a solr document given a list of fieldname/value pairs
        example: update_document("bd74c030-3161-4962-9f98-47f6d00c89cc", [{"field_value": "value1", "field_name": "field1_s"}, {"field_value": "value2", "field_name": "field2_s"}])
        @param record_identifier: record identifier (solr identifier)
        @param kv_pairs: list of fieldname/value pairs
        @return: status code
        """
        url_suffix = 'update'
        update_url = self.solr_instance + url_suffix
        update_headers = {'Content-Type': 'application/json'}
        update_data = dict()
        update_data[self.solr_unique_key] = record_identifier
        for kv_pair in kv_pairs:
            update_data[kv_pair['field_name']] = {'set': kv_pair['field_value']}
        update_doc = json.dumps([update_data])
        update = requests.post(update_url, data=update_doc, headers=update_headers)

        print update_url
        print json.dumps([update_data], indent=4)
        return update.status_code

    def get_doc_id_from_path(self, safe_urn_identifier, entry_path):
        """
        Get identifier from solr document
        @param safe_urn_identifier: safe identifier, e.g. urn\:uuid\:0426f626-d51d-449c-84fa-d5c32d728509
        @param entry_path: entry path, e.g. /submission/representations/rep1/data/Example1.docx
        @return: document identifier, e.g. "d66c0d7b-0b9d-4a4f-a1d5-7d829f109018"
        """
        query_result = self.send_query('path:%s%s' % (safe_urn_identifier, entry_path))
        if query_result is False:
            raise RuntimeError("No query result")
        identifier = None
        if "lily.key" in query_result[0]:
            identifier = query_result[0]['lily.key']
        else:
            identifier = query_result[0]['id']
        if not identifier:
            raise RuntimeError("Unable to get document identifier")
        return identifier

    # def add_to_field(self, record_identifier, field, content):
    #     """
    #     Add a new entry to a field. Existing field needs to be a multi-valued string field (a list).
    #     @param record_identifier:
    #     @param field:
    #     @param content:
    #     @return:
    #     """
    #     # TODO: field needs to be multi-valued string (adding to a list)
    #     url_suffix = 'update'
    #     add_url = self.solr_instance + url_suffix
    #     update_headers = {'Content-Type': 'application/json'}
    #     update_data = json.dumps([{field: {'add': content}, self.solr_unique_key: record_identifier}])
    #     update = requests.post(add_url, data=update_data, headers=update_headers)
    #     return update.status_code

    # def remove_from_field(self):
    #     # remove from a field (which needs to be a list)
    #     pass
