import os
from urlparse import urljoin
import unittest
from config.configuration import test_rest_endpoint_hdfs_upload

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
        rest_endpoint = RestEndpoint(test_rest_endpoint_hdfs_upload, "dm-hdfs-storage")
        self.assertEqual(rest_endpoint.to_string(), "%s/dm-hdfs-storage" % test_rest_endpoint_hdfs_upload)
        self.assertEqual(rest_endpoint.get_resource_uri("hsink/fileresource/files/{0}"), "%s/dm-hdfs-storage/hsink/fileresource/files/{0}" % test_rest_endpoint_hdfs_upload)

if __name__ == '__main__':
    unittest.main()