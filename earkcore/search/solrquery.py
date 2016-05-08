"""Solr query"""
import unittest


def default_reporter(percent):
    print "\rProgress: {percent:3.0f}%".format(percent=percent)


class SolrQuery(object):

    server = None
    port = None

    def __init__(self, server, port):
        """
        Constructor to initialise solr client API URL

        @type       server: string
        @param      server: Solr base url, e.g. "http://localhost:8983/solr/"

        @type       port: int
        @param      port: port number
        """
        self.server = server
        self.port = port

    def get_select_pattern(self, core):
        """
        Get select url pattern

        @type       core: string
        @param      core: name of solr core

        @rtype: string
        @return: select url pattern
        """
        server_solr_query_url = "http://%s:%d/solr/%s/select?q={0}&wt=json" % (self.server, self.port, core)
        return server_solr_query_url


class TestSolrQuery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_extract(self):
        sq = SolrQuery("127.0.0.1", 8888)
        self.assertEqual("http://127.0.0.1:8888/solr/eark/select?q={0}&wt=json", sq.get_select_pattern("eark"))

if __name__ == '__main__':
    unittest.main()
