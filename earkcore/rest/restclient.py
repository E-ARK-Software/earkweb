#!/usr/bin/env python
# coding=UTF-8
from earkcore.rest.restendpoint import RestEndpoint
# test_client.py
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2

__author__ = "Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
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
        @type       str: string
        @param      str: Some string
        @rtype:     bool
        @return:    Validity
        """
        uri = self.rest_endpoint.get_resource_uri(resource)
        #field:rdf	abc.ttl --> abc "name"

        register_openers()

        datagen, headers = multipart_encode({field_name: open(file_path, "r")})

        request = urllib2.Request(uri, datagen, headers)

        response = urllib2.urlopen(request)
        print response

        return True


class RestClientTest(unittest.TestCase):
    from config.configuration import peripleo_server_ip, peripleo_port, peripleo_path
    rest_endpoint = RestEndpoint("http://%s:%s" % (peripleo_server_ip, peripleo_port), peripleo_path)
    my_instance = RestClient(rest_endpoint)

    def test_do_post(self):
        """
        Must return true
        """
        test_file = "/var/data/earkweb/work/1f1576d2-fcea-43be-a0c9-7051f7116ae6/representations/peripleottl/data/ob_1994.ttl"
        print RestClientTest.my_instance.post_file("admin/gazetteers", "rdf", test_file)


if __name__ == '__main__':
    unittest.main()