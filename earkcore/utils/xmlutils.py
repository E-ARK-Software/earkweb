from xml.dom.minidom import parseString
from xml.etree import ElementTree
from xml.dom import minidom
import os
from earkcore.utils.fileutils import read_file_content
from earkcore.xml.xmlschemanotfound import XMLSchemaNotFound
import lxml.etree as ET

def pretty_xml_string(xml_string):
    xml = parseString(xml_string)
    return xml.toprettyxml()

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def get_xml_schemalocations(xml_file):
    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    xml_dir, tail = os.path.split(xml_file)
    xml_content = read_file_content(xml_file)
    tree = ET.XML(xml_content)
    schema_locs = []
    #Find instances of xsi:schemaLocation
    schema_locations = set(tree.xpath("//*/@xsi:schemaLocation", namespaces={'xsi': XSI}))
    for schema_location in schema_locations:
        namespaces_locations = schema_location.strip().split()
        # Import all fnamspace/schema location pairs
        for namespace, location in zip(*[iter(namespaces_locations)] * 2):
            loc = os.path.abspath(os.path.join(xml_dir, location))
            if not os.path.exists(loc):
                print "ERROR: XML-Schema file not found: %s" % loc
                raise XMLSchemaNotFound("XML-Schema file not found: %s" % loc)
            schema_locs.append(loc)
    return schema_locs