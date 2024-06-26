"""Solr query"""
import unittest


def default_reporter(percent):
    print("\rProgress: {percent:3.0f}%".format(percent=percent))


class SolrServer(object):

    protocol = None
    server = None
    port = None

    def __init__(self, protocol, server, port):
        """
        Constructor to initialise solr client API URL

        @type       server: string
        @param      server: Solr base url, e.g. "http://localhost:8983/solr/"

        @type       port: int
        @param      port: port number
        """
        self.protocol = protocol
        self.server = server
        self.port = port

    def get_base_url(self):
        """
        Get select url pattern

        @rtype: string
        @return: base url
        """
        return "%s://%s:%d/solr/" % (self.protocol, self.server, self.port)


class TestSolrServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_extract(self):
        sq = SolrServer("http", "127.0.0.1", 8888)
        self.assertEqual("http://127.0.0.1:8888/solr/", sq.get_base_url())

if __name__ == '__main__':
    unittest.main()
