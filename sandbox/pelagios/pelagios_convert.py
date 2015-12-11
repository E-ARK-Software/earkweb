"""
Pelagios RDF
"""

from rdflib import Namespace, Literal, URIRef
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
from rdflib import RDF, BNode
from gml_to_wkt import GMLtoWKT
from gml_to_wkt_helper import whsp_to_unsc


if __name__ == '__main__':
    jahre = ["1994", "1995", "1998", "2002", "2006", "2010", "2015"]

    uris = {
        "1994": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/34809536-b9f8-4c51-83d1-ef365ca658f5/",
        "1995": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/1ca1ee45-9468-4ea3-a67d-b20e1dc9e43a/",
        "1998": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/5f1ce541-2e27-4aca-bcb2-bb567436386e/",
        "2002": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/b1536bef-22f2-41cc-bcad-8229b64b191c/",
        "2006": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/eecc209d-99a6-446d-9a9b-bee2784d6dd2/",
        "2010": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/c4795a65-2b60-4a4a-8bbb-a9e62755ca9c/",
        "2015": "http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/b5cd7779-b445-408c-87dd-7be643df3599/" }

    for jahr in jahre:

        print "Jahr: %s" % jahr
        print "-------------------------------------------------"

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
        gml_to_wkt = GMLtoWKT('/home/shs/slovenia/ob_%s.gml' % jahr)
        district_included = {}
        for district_wkt in gml_to_wkt.get_wkt_linear_ring():
            techname = whsp_to_unsc(district_wkt["name"])
            if not techname in district_included:
                # http://earkdev.ait.ac.at/earkweb/sip2aip/working_area/sip2aip/a0201326-f701-4ba9-ba6e-cd881c7a2c73/#place/%s/%s
                district = URIRef("%s#place/%s/%s" % (uris[jahr], whsp_to_unsc(district_wkt["name"]), jahr))
                graph_slovenian_districts.add((district, RDF.type, lawd_ns.Place))
                graph_slovenian_districts.add((district, dcterms_ns['isPartOf'], slovenia))
                graph_slovenian_districts.add((district, dcterms_ns['temporal'], Literal(str(district_wkt["year"]))))
                graph_slovenian_districts.add((district, gn_ns['countryCode'], Literal(u'SI')))
                graph_slovenian_districts.add((district, rdfs_ns['label'], Literal(district_wkt["name"], lang=u'si')))
                polygons = BNode()
                graph_slovenian_districts.add((district, geosparql_ns['hasGeometry'], polygons))
                g.add((polygons, geosparql_ns['asWKT'], Literal(district_wkt["polygon"])))
                district_included[techname] = True
        # print graph
        output_file = "/home/shs/slovenia/ob_%s.ttl" % jahr
        with open(output_file, 'w') as f:
            f.write(g.serialize(format='n3'))
        f.close()

        print "Output written to %s" % output_file