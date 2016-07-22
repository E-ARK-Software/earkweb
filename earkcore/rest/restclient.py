#!/usr/bin/env python
# coding=UTF-8
import logging
import os
from earkcore.rest.restendpoint import RestEndpoint
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
logger = logging.getLogger(__name__)
from config.configuration import root_dir

__author__ = "Sven Schlarb"
__copyright__ = "Copyright 2016, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

import unittest


class RestClient(object):
    """
    REST client class
    """

    rest_endpoint = None

    def __init__(self, rest_endpoint):
        """
        Constructor to initialise Rest Client with end point and progress reporter function
        @type       rest_endpoint: earkcore.rest.RestEndpoint
        @param      rest_endpoint: REST Endpoint (protocol, server-name, api)
        """
        self.rest_endpoint = rest_endpoint

    def post_file(self, resource, field_name, file_path):
        """
        Post file
        @type       resource: string
        @param      resource: Resource path of the REST request
        @type       field_name: string
        @param      field_name: Field name of the file to be posted
        @type       file_path: string
        @param      file_path: Path to the file to be posted
        @rtype:     bool
        @return:    Indicates if the post request was successful
        """
        uri = self.rest_endpoint.get_resource_uri(resource)
        try:
            register_openers()
            datagen, headers = multipart_encode({field_name: open(file_path, "r")})
            request = urllib2.Request(uri, datagen, headers)
            urllib2.urlopen(request)
            logger.info("Successfully posted file: %s to %s" % (file_path, uri))
            return True
        except IOError, e:
            logger.error("An error occurred: %s " % e.message)
            return False
        except urllib2.HTTPError, e:
            logger.error("An error occurred: %s (%d)" % (e.reason, e.code))
            return False
        except urllib2.URLError, e:
            logger.error("An error occurred: %s" % e.reason)
            return False


class RestClientTest(unittest.TestCase):

    from config.configuration import peripleo_server_ip, peripleo_port, peripleo_path
    rest_endpoint = RestEndpoint("http://%s:%s" % (peripleo_server_ip, peripleo_port), peripleo_path)
    my_instance = RestClient(rest_endpoint)

    def test_do_post(self):
        """
        Test post request
        """
        # Test deactivated because it requires a running Peripleo instance
        pass
        #test_file = os.path.join(root_dir, "earkresources/geodata/ob_2015.ttl")
        #print RestClientTest.my_instance.post_file("admin/gazetteers", "rdf", test_file)


if __name__ == '__main__':
    unittest.main()
