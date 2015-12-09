from itertools import izip


#ns = {'ogr': 'http://ogr.maptools.org/', 'gml': 'http://www.opengis.net/gml/3.2'}
ns = {'ogr': 'http://ogr.maptools.org/', 'gml': 'http://www.opengis.net/gml'}


def format_location_name(location_name):
    """
    Format parts of a name
    :type location_name: location name
    :param location_name: location name
    :return: First letter upper case, rest lower case
    """
    parts = []
    for part in location_name.split(" "):
        ps = []
        for p in part.split("-"):
            ps.append(first_upper_rest_lower(p))
        parts.append("-".join(ps))
    return " ".join(parts)


def first_upper_rest_lower(strval):
    """
    First letter upper case, rest lower case
    :type strval: string
    :param strval: string value
    """
    return strval[0:1].upper()+strval[1:len(strval)].lower()


def get_number_suffix(strval):
    """
    Get number suffix
    :param strval: string value
    :return: number suffix (int)
    """
    number_suffix = 0
    if len(strval) > 4:
        number_suffix_str = strval[-4:len(strval)]
        if number_suffix_str.isdigit():
            number_suffix = int(number_suffix_str)
    return number_suffix


def pairwise(iterable):
    """
    Helper function to iterate pairwise.
    :param iterable: values list
    :return: tuple
    """
    a = iter(iterable)
    return izip(a, a)


def tagname(elm):
    """
    Get tagname from fully qualified tag string
    :param elm: Etree element
    :return: tagname
    """
    uri, tag = elm.tag[1:].split("}")
    return tag


def whsp_to_unsc(strval):
    """
    White spaces to underscore
    :type strval: string
    :param strval: string value
    """
    return strval.replace(' ', '_')
