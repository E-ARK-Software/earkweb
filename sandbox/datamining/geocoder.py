import os
import unittest
import codecs
import time
from geopy.geocoders import Nominatim
from lxml import etree, objectify

L = objectify.ElementMaker(
    annotate=False)

class Geocoder():
    def __init__(self):
        self.geolocator = Nominatim()

    def get_coordinates(self, name):
        loc = self.geolocator.geocode(name)
        if loc is not None:
            # location = '%s %f %f \n' % (loc[0].encode('utf-8'), loc.latitude, loc.longitude)
            return loc.latitude, loc.longitude
            #with codecs.open('/var/data/nlp/presse_subset/sub_locations.txt', 'a') as output:
            #    output.write(location)
        return '', ''



class testGeocoder(unittest.TestCase):

    def testGeocoding(self):
        coords = Geocoder()

        root = L.geocodes({})

        with codecs.open('/var/data/nlp/presse_subset/clean_locations.txt', 'r') as input:
            for entity in input.readlines():
                entity.strip('\n')
                print 'Nominatim call for: %s' % entity
                lat, long = coords.get_coordinates(entity)
                geo = L.georesult({'name': entity.input_json('utf-8'),
                                   'latitude': lat,
                                   'longitude': long,
                                   'idf': ''})
                root.append(geo)
                time.sleep(1.1)

            str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
            path_loc_xml = os.path.join('/var/data/nlp/presse_subset/', 'geocodes.xml')
            with open(path_loc_xml, 'w') as output_file:
                output_file.write(str)


if __name__ == '__main__':
    unittest.main()