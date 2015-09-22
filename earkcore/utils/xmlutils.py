from xml.dom.minidom import parseString


def pretty_xml_string(xml_string):
    xml = parseString(xml_string)
    return xml.toprettyxml()


def tagname(elm):
    """
    Get tagname from fully qualified tag string
    :param elm: Etree element
    :return: tagname
    """
    uri, tag = elm.tag[1:].split("}")
    return tag
