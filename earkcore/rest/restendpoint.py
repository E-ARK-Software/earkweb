import os
from urlparse import urljoin
import unittest

class RestEndpoint:

    base = None
    api = None

    def __init__(self, base, api):
        self.base = base
        self.api = api

    def get_endpoint_uri(self):
        return urljoin(self.base, self.api)

    def get_resource_uri(self, resource_path):
        return urljoin(self.get_endpoint_uri(), os.path.join(self.api, resource_path))

    def to_string(self):
        return urljoin(self.base, self.api)

class TestRestEndpoint(unittest.TestCase):


    def test_rest_endpoint(self):
        rest_endpoint = RestEndpoint("http://81.189.135.189", "dm-hdfs-storage")
        self.assertEqual(rest_endpoint.to_string(), "http://81.189.135.189/dm-hdfs-storage")
        self.assertEqual(rest_endpoint.get_resource_uri("hsink/fileresource/files/{0}"), "http://81.189.135.189/dm-hdfs-storage/hsink/fileresource/files/{0}")

if __name__ == '__main__':
    unittest.main()