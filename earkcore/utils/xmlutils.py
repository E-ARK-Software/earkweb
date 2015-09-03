from xml.dom.minidom import parseString

def pretty_xml_string(xml_string):
    xml = parseString(xml_string)
    return xml.toprettyxml()