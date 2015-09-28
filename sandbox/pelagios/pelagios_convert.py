"""
Pelagios RDF
"""

from rdflib import Namespace, Literal, URIRef
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
from rdflib import RDF, BNode
from sandbox.pelagios.gml_to_wkt import GMLtoWKT
from sandbox.pelagios.gml_to_wkt_helper import whsp_to_unsc


if __name__ == '__main__':

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

    slovenia = URIRef("http://www.mygazetteer.org/place/Slovenia")

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

    gml_to_wkt = GMLtoWKT('./Obcine1994.gml')
    district_included = {}
    for district_wkt in gml_to_wkt.get_wkt_linear_ring():
        techname = whsp_to_unsc(district_wkt["name"])
        if not techname in district_included:
            district = URIRef("http://www.mygazetteer.org/place/%s" % whsp_to_unsc(district_wkt["name"]))
            graph_slovenian_districts.add((district, RDF.type, lawd_ns.Place))
            graph_slovenian_districts.add((district, dcterms_ns['isPartOf'], slovenia))
            graph_slovenian_districts.add((district, dcterms_ns['temporal'], Literal(str(district_wkt["year"]))))
            graph_slovenian_districts.add((district, gn_ns['countryCode'], Literal(u'SI')))
            graph_slovenian_districts.add((district, dcterms_ns['label'], Literal(district_wkt["name"], lang=u'si')))
            polygons = BNode()
            graph_slovenian_districts.add((district, geosparql_ns['hasGeometry'], polygons))
            g.add((polygons, geosparql_ns['asWKT'], Literal(district_wkt["linearring"])))
            district_included[techname] = True
    # print graph
    output_file = "Opcine1994.rdf"
    with open(output_file, 'w') as f:
        f.write(g.serialize(format='n3'))
    f.close()

    print "Output written to %s" % output_file