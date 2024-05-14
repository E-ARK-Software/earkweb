"""Solr query"""
import unittest
from .solrserver import SolrServer


def default_reporter(percent):
    print("\rProgress: {percent:3.0f}%".format(percent=percent))


class SolrQuery(object):

    solr_server = None

    def __init__(self, solr_server):
        """
        Constructor to initialise solr client API URL

        @type       server: SolrServer
        @param      server: Solr server
        """
        self.solr_server = solr_server

    def get_base_url(self):
        """
        Get select url pattern

        @rtype: string
        @return: base url
        """
        return "%s://%s:%d/solr/" % (self.solr_server.protocol, self.solr_server.server, self.solr_server.port)

    def get_select_pattern(self, core):
        """
        Get select url pattern

        @type       core: string
        @param      core: name of solr core

        @rtype: string
        @return: select url pattern
        """
        qurl = "%s://%s:%d/solr/%s/select?q={0}&wt=json" % (self.solr_server.protocol, self.solr_server.server, self.solr_server.port, core)
        return qurl


class TestSolrQuery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_extract(self):
        sq = SolrQuery(SolrServer("http", "127.0.0.1", 8888))
        self.assertEqual("http://127.0.0.1:8888/solr/earkweb/select?q={0}&wt=json", sq.get_select_pattern("earkweb"))

if __name__ == '__main__':
    unittest.main()
