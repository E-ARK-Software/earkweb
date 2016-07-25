"""
Peripleo GML to TTL (RDF) conversion
"""
import os
import shutil

from rdflib import Namespace, Literal, URIRef
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
from rdflib import RDF, BNode
from config.configuration import root_dir
from earkcore.utils import randomutils
from earkcore.utils.randomutils import randomword
from gml_to_wkt import GMLtoWKT
import unittest

from xml.etree import ElementTree
from gml_to_wkt_helper import *
from earkcore.process.processor import Processor


class PeripleoGmlProcessing(Processor):
    """
    MyClass class
    """
    gml_file = None
    valid = None

    def __init__(self, gml_file):
        """
        @type       gml_file: string
        @param      gml_file: Absolute path to GML file
        """
        self.gml_file = gml_file
        super(PeripleoGmlProcessing, self).__init__()

    def conversion_conditions_fulfilled(self):
        tree = ElementTree.parse(self.gml_file)
        num_feature_members = sum(1 for _ in tree.iter('{http://www.opengis.net/gml}featureMember'))
        if num_feature_members == 0:
            self.err.append("No feature members found in GML file (element featureMember in namespace 'http://www.opengis.net/gml').")
            return False
        else:
            self.log.append("%d feature elements found." % num_feature_members)
        for feature_member in tree.iter('{http://www.opengis.net/gml}featureMember'):
            for district in feature_member:
                from gml_to_wkt_helper import ns as ogr_ns
                distr_name_candidates = ['OB_ATR_D46_IME', 'OB_ATR_OB_IME']
                district_name_elm = None
                distr_name = None
                for distr_name_candidate in distr_name_candidates:
                    district_name_elm = district.find("ogr:%s" % distr_name_candidate, ogr_ns)
                    if district_name_elm is not None:
                        distr_name = format_location_name(district_name_elm.text)
                        break
                if district_name_elm is None:
                    self.err.append("Feature has no valid district name" % distr_name)
                    return False
        return True

    def convert_gml(self, ttl_output_file, uri_part, specific_part):
            """
            Pelagios conversion GML to TTL
            @type       ttl_output_file: string
            @param      ttl_output_file: Absolute path to TTL output file
            @type       uri_part: string
            @param      uri_part: URI for the region to be displayed (e.g. http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/34809536-b9f8-4c51-83d1-ef365ca658f5/)
            @type       specific_part: string
            @param      specific_part: Specific part that distinguishes the URI from other URIs (e.g. 1994)
            """
            cito_ns = Namespace("http://purl.org/spar/cito")
            cnt_ns = Namespace("http://www.w3.org/2011/content#")
            dcterms_ns = Namespace("http://purl.org/dc/terms/")
            foaf_ns = Namespace("http://xmlns.com/foaf/0.1/")
            geo_ns = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
            geosparql_ns = Namespace("http://www.opengis.net/ont/geosparql#")
            gn_ns = Namespace("http://www.geonames.org/ontology#")
            lawd_ns = Namespace("http://lawd.info/ontology/")
            rdfs_ns = Namespace("http://www.w3.org/2000/01/rdf-schema#")
            skos_ns = Namespace("http://www.w3.org/2004/02/skos/core#")

            slovenia = URIRef("http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/5c6f5563-7665-4719-a2b6-4356ea033c1d/#place/Slovenia")

            store = IOMemory()

            g = ConjunctiveGraph(store=store)
            g.bind("cito", cito_ns)
            g.bind("cnt", cnt_ns)
            g.bind("dcterms", dcterms_ns)
            g.bind("foaf", foaf_ns)
            g.bind("geo", geo_ns)
            g.bind("geosparql", geosparql_ns)
            g.bind("gn", gn_ns)
            g.bind("lawd", lawd_ns)
            g.bind("rdfs", rdfs_ns)
            g.bind("skos", skos_ns)

            graph_slovenian_districts = Graph(store=store, identifier=slovenia)
            gml_to_wkt = GMLtoWKT(self.gml_file)
            district_included = {}
            i = 1
            print "Processing GML file: %s" % self.gml_file
            for district_wkt in gml_to_wkt.get_wkt_linear_ring():
                techname = whsp_to_unsc(district_wkt["name"])
                print "District %d: %s" % (i, whsp_to_unsc(district_wkt["name"]))
                if techname not in district_included:
                    district = URIRef("%s#place/%s/%s" % (uri_part, whsp_to_unsc(district_wkt["name"]), specific_part))
                    graph_slovenian_districts.add((district, RDF.type, lawd_ns.Place))
                    graph_slovenian_districts.add((district, dcterms_ns['isPartOf'], slovenia))
                    graph_slovenian_districts.add((district, dcterms_ns['temporal'], Literal(str(district_wkt["year"]))))
                    graph_slovenian_districts.add((district, gn_ns['countryCode'], Literal(u'SI')))
                    graph_slovenian_districts.add((district, rdfs_ns['label'], Literal(district_wkt["name"], lang=u'si')))
                    polygons = BNode()
                    graph_slovenian_districts.add((district, geosparql_ns['hasGeometry'], polygons))
                    g.add((polygons, geosparql_ns['asWKT'], Literal(district_wkt["polygon"])))
                    district_included[techname] = True
                i += 1
            with open(ttl_output_file, 'w') as f:
                f.write(g.serialize(format='n3'))
            f.close()


class TestPelagiosConversion(unittest.TestCase):

    gml_data_dir = root_dir + '/earkresources/geodata'
    temp_result_dir = root_dir + '/tmp/temp-' + randomutils.randomword(10)

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TestPelagiosConversion.temp_result_dir):
            os.makedirs(TestPelagiosConversion.temp_result_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TestPelagiosConversion.temp_result_dir)

    def convert_gml_to_ttl(self, file_name):
        gml_file_path = os.path.join(TestPelagiosConversion.gml_data_dir, file_name)
        path, gml_file = os.path.split(gml_file_path)
        file_name, ext = os.path.splitext(gml_file)
        ttl_file_path = os.path.join(TestPelagiosConversion.temp_result_dir, "%s.ttl" % file_name)
        file_name_parts = file_name.split("_")
        specific_part = randomword(5) if len(file_name_parts) != 2 else file_name_parts[1]
        uri_part = "http://%s:%s/earkweb/sip2aip/working_area/aip2dip/%s/" % ("127.0.0.1", "8000", "abcdefghijklmnopq")
        gml_proc = PeripleoGmlProcessing(gml_file_path)
        gml_proc.convert_gml(ttl_file_path, uri_part, specific_part)

    def test_convert_gml_to_ttl_1994(self):
        self.convert_gml_to_ttl("ob_1994.gml")

    def test_convert_gml_to_ttl_1995(self):
        self.convert_gml_to_ttl("ob_1995.gml")

    def test_convert_gml_to_ttl_1998(self):
        self.convert_gml_to_ttl("ob_1998.gml")

    def test_convert_gml_to_ttl_2002(self):
        self.convert_gml_to_ttl("ob_2002.gml")

    def test_convert_gml_to_ttl_2006(self):
        self.convert_gml_to_ttl("ob_2006.gml")

    def test_convert_gml_to_ttl_2010(self):
        self.convert_gml_to_ttl("ob_2010.gml")

    def test_convert_gml_to_ttl_2015(self):
        self.convert_gml_to_ttl("ob_2015.gml")


if __name__ == '__main__':
    unittest.main()
