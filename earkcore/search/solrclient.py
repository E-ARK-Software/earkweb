"""Simple model of Apache Solr 1.4 and 3.x"""
import os
import json
import shutil
import urllib
import urllib2

import lxml.etree as etree
import unittest

import requests

from earkcore.utils import randomutils


class SolrClient(object):

    """
    Constructor to initialise solr client API URL

    @type       base_url: string
    @param      base_url: Solr base url, e.g. "http://localhost:8983/solr/"

    @type       collection: string
    @param      collection: Collection identifier, e.g. "samplecollection"
    """
    def __init__(self, base_url, collection):
        if base_url[-1] != '/':
            base_url += '/'
        self.url = base_url + collection

    """
    Search Solr, return URL and JSON response

    @type       params: string
    @param      params: Query parameters

    @rtype: string, int
    @return: Return url and return code
    """
    def select(self, params):
        params['wt'] = 'json'
        url = self.url + '/select?' + urllib.urlencode(params)
        conn = urllib2.urlopen(url)
        return url, json.load(conn)

    """
    Delete query result documents

    @type       query: string
    @param      query: query

    @rtype: string, int
    @return: Return url and return code
    """
    def delete(self, query):
        params = {}
        url = self.url + '/update?' + urllib.urlencode(params)
        request = urllib2.Request(url)
        request.add_header('Content-Type', 'text/xml; charset=utf-8')
        request.add_data('<delete><query>{0}</query></delete>'.format(query))
        response = urllib2.urlopen(request).read()
        status = etree.XML(response).findtext('lst/int')
        return url, status

    """
    Post a list of documents

    @type       docs: list
    @param      docs: List of solr documents

    @rtype: string, int
    @return: Return url and return code
    """
    def update(self, docs):
        url = self.url + '/update?commit=true'
        add_xml = etree.Element('add')
        for doc in docs:
            xdoc = etree.SubElement(add_xml, 'doc')
            for key, value in doc.iteritems():
                if value:
                    field = etree.Element('field', name=key)
                    field.text = (value if isinstance(value, unicode)
                                  else str(value))
                    xdoc.append(field)
        request = urllib2.Request(url)
        request.add_header('Content-Type', 'text/xml; charset=utf-8')
        request.add_data(etree.tostring(add_xml, pretty_print=True))
        response = urllib2.urlopen(request).read()
        status = etree.XML(response).findtext('lst/int')
        return url, status

    """
    Iterate over tar file and post documents it contains to Solr API (extract)

    @type       tar_file_path: string
    @param      tar_file_path: Absolute path to tar file

    @type       identifier: string
    @param      identifier: Identifier of the tar package

    @rtype: list(dict(string, int))
    @return: Return list of urls and return codes
    """
    def post_tar_file(self, tar_file_path, identifier):
        import tarfile
        tfile = tarfile.open(tar_file_path, 'r')
        extract_dir = '/tmp/temp-' + randomutils.randomword(10)
        results = []
        for t in tfile:
            tfile.extract(t, extract_dir)
            afile = os.path.join(extract_dir, t.name)
            if os.path.exists(afile):
                files = {'file': ('userfile', open(afile, 'rb'))}
                post_url = '%s/update/extract?literal.package=%s&literal.entry=%s' % (self.url, identifier, t.name)
                response = requests.post(post_url, files=files)
                result = {"url": post_url, "status": response.status_code}
                results.append(result)
        self.commit()
        shutil.rmtree(extract_dir)
        return results

    """
    Commit changes to Solr

    @rtype: string, int
    @return: Return url and return code
    """
    def commit(self):
        url = self.url + '/update?commit=true'
        response = urllib2.urlopen(url)
        return url, response.code


class TestSolr(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    # def test_solr_post_document(self):
    #     slr = SolrClient("http://localhost:8983/solr/", "samplecollection")
    #     docs = []
    #     document = {"id":"1234abcde",
    #             "cat":"journal",
    #             "name":"Experiments on the go",
    #             "genre_s":"science"}
    #     docs.append(document)
    #     slr.update(docs)
    #     slr.commit()

    # def test_extract(self):
    #     slr = SolrClient("http://localhost:8983/solr/", "samplecollection")
    #     tar_file_path = "/opt/python_wsgi_apps/earkweb/earkresources/storage-test/bar.tar"
    #     identifier = "739f9c5f-c402-42af-a18b-3d0bdc4e8751"
    #     results = slr.post_tar_file(tar_file_path, identifier)
    #     print results

if __name__ == '__main__':
    unittest.main()
