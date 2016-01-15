"""
Pelagios RDF
"""

from rdflib import Namespace, Literal, URIRef
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
from rdflib import RDF, BNode
# from gml_to_wkt import GMLtoWKT
# from gml_to_wkt_helper import whsp_to_unsc

from lxml import etree

if __name__ == '__main__':
    ausgaben = ["18751113", "18751114", "18751117", "18751118", "18751119", "18751120", "18751121", "18751123"]

    uris = {"18751113": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751113&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751114": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751114&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751117": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751117&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751118": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751118&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751119": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751119&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751120": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751120&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751121": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751121&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22",
            "18751123": "http://anno.onb.ac.at/cgi-content/anno?aid=apr&datum=18751123&provider=ENP&ref=anno-search&query=%22Die%22+%22Presse%22"}

    for ausgabe in ausgaben:

        print "Ausgabe: %s" % ausgabe
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

        newspaper = URIRef('http://anno.onb.ac.at/anno-suche/#searchMode=complex&title=Die+Presse&resultMode=calendar&year=1875&month=11')
        # newspaper = URIRef('http://anno.onb.ac.at')

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

        graph_newspaper_geo = Graph(store=store, identifier=newspaper)

        source = etree.parse("/var/data/earkweb/work/newspapers/ner/%s_tokenized.xml" % ausgabe).getroot()
        location_included = {}
        for child in source.getchildren():
            name = child.attrib['name']
            if not name in location_included:
                lat = child.attrib['latitude']
                long = child.attrib['longitude']
                coordinates = 'POINT (%s %s)' % (long, lat)

                date = '%s-%s-%s' % (ausgabe[:4], ausgabe[-4:-2], ausgabe[:2])
                # date = ausgabe[:4]

                location_name = URIRef('%s#place/%s' % (uris[ausgabe], name))
                # location_name = URIRef('%s#place/%s' % (ausgabe, name))

                graph_newspaper_geo.add((location_name, RDF.type, lawd_ns.Place))
                graph_newspaper_geo.add((location_name, dcterms_ns['isPartOf'], newspaper))
                graph_newspaper_geo.add((location_name, dcterms_ns['temporal'], Literal(date)))
                graph_newspaper_geo.add((location_name, gn_ns['countryCode'], Literal(u'AUT')))
                graph_newspaper_geo.add((location_name, rdfs_ns['label'], Literal(name, lang=u'de')))
                point = BNode()
                graph_newspaper_geo.add((location_name, geosparql_ns['hasGeometry'], point))
                g.add((point, geosparql_ns['asWKT'], Literal(coordinates)))

                location_included[name] = True


        # print graph
        output_file = "/home/janrn/newspapers/ob_%s.ttl" % ausgabe
        with open(output_file, 'w') as f:
            f.write(g.serialize(format='n3'))
        f.close()

        print "Output written to %s" % output_file