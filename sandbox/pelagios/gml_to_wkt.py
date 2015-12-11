from xml.etree import ElementTree
from shapely.geometry.polygon import LinearRing
from shapely.geometry.polygon import Polygon
from gml_to_wkt_helper import *
from pyproj import Proj, transform

def flat_pos_list_to_coord_tuples(flat_pos_list):
    """
    Convert a list of position values (element gml:posList) into a coordinate tuples list.
    flat_pos_list must have even number of position values ((x1, y1), (x2, y2), (xn, yn), etc., (x1, y1)),
    the first being the X and the second the Y coordinate. The coordinates of the polygon must be closed,
    i.e. the first tuple must equal the last tuple.
    :type flat_pos_list: list
    :param flat_pos_list: flat list of coordinates
    :return: list of coordinate tuples (float)
    """
    if flat_pos_list < 6:
        raise ValueError("Not enough values")
    if flat_pos_list[0] != flat_pos_list[len(flat_pos_list)-2] or flat_pos_list[1] != flat_pos_list[len(flat_pos_list)-1]:
        raise ValueError("Not a closed polygon (first tuple must equal last tuple)")
    coordinate_tuples = []
    inProj = Proj(init='epsg:3912')
    outProj = Proj(init='epsg:4326')
    if flat_pos_list >= 6 and len(flat_pos_list) % 2 == 0:
        for x, y in pairwise(flat_pos_list):
            # transform
            x_t, y_t = transform(inProj, outProj, x, y)
            coordinate_tuples.append((float(x_t), float(y_t)))
    else:
        raise ValueError("even number of coordinate tuples required")
    return coordinate_tuples


def get_pos_list_from_gml(elm, geometry_path, pos_list_path):
    """
    Get list of position tuples (flat list) from gml document.
    :param elm: element where matching starts
    :param geometry_path: path to geometry property (polygon)
    :param pos_list_path: gml elements path to posList element
    :return: list of position tuples (flat list)
    """
    geometry_elm = elm.find(geometry_path, ns)
    pos_list_elms = geometry_elm.findall(pos_list_path, ns)
    p_list = None
    if len(pos_list_elms) == 1:
        pos_list_elm = pos_list_elms[0]
        data = pos_list_elm.text.replace(",", " ")
        p_list = data.split()
    return p_list


class GMLtoWKT(object):

    def __init__(self, gml_file):
        self.tree = ElementTree.parse(gml_file)

    def get_wkt_linear_ring(self):
        """
        Get WKT LINEARRING dictionary
        :return: linering dictionary generator
        <gml:featureMember>
        <ogr:slov_reg_1994 fid="slov_reg_1994.0">
        <ogr:geometryProperty><gml:Polygon srsName="EPSG:4326"><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>

        <ogr:geometryProperty><gml:Polygon srsName="EPSG:4326"><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>
        """
        for feature_member in self.tree.iter('{http://www.opengis.net/gml}featureMember'):
            for district in feature_member:
                district_name_elm = district.find("ogr:OB_ATR_OB_IME", ns) #
                distr_name = format_location_name(district_name_elm.text)
                print "Region: %s" % distr_name
                pos_list = get_pos_list_from_gml(district, 'ogr:geometryProperty', 'gml:Polygon/gml:outerBoundaryIs/gml:LinearRing/gml:coordinates')
                linearing = flat_pos_list_to_coord_tuples(pos_list)
                year = get_number_suffix(tagname(district))
                yield {"name": distr_name, "year": year,  "polygon": Polygon(linearing).wkt}


if __name__ == '__main__':
    gml_to_wkt = GMLtoWKT('/home/shs/slovenia/ob_1995.ttl')
    i = 0
    for district in gml_to_wkt.get_wkt_linear_ring():
        print "%s (%d) %d" % (district["name"], district["year"], i)
        # print district["linearring"]
        i += 1
