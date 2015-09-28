from xml.dom.minidom import parseString
from xml.etree import ElementTree
from xml.dom import minidom

def pretty_xml_string(xml_string):
    xml = parseString(xml_string)
    return xml.toprettyxml()

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")