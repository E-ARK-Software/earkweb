import os
import unittest
import codecs
import time
from geopy.geocoders import Nominatim
from lxml import etree, objectify

L = objectify.ElementMaker(
    annotate=False)

class Geocoder():
    def __init__(self, path):
        self.geolocator = Nominatim()
        self.path = path

    def removeDuplicates(self):
        names_no_duplicates = ''
        with codecs.open(os.path.join(self.path, 'locations.txt'), 'rw') as loc:
            all_names = loc.readlines()
            # remove all entries that appear more than once - to avoid superfluous geocoder API calls
            for name in list(set(all_names)):
                names_no_duplicates += name

        with codecs.open(os.path.join(self.path, 'clean_locations.txt'), 'w') as output:
            for name in names_no_duplicates:
                output.write(name)

    def get_coordinates(self):
        root = L.geocodes({})

        with codecs.open(os.path.join(self.path, 'clean_locations.txt'), 'r') as input:
            for entity in input.readlines():
                entity.strip('\n')
                print 'Nominatim call for: %s' % entity

                loc = self.geolocator.geocode(entity)
                if loc is not None:
                    lat = loc.latitude
                    long = loc.longitude
                else:
                    lat = ''
                    long = ''

                geo = L.georesult({'name': entity.decode('utf-8'),
                                   'latitude': lat,
                                   'longitude': long,
                                   'idf': ''})
                root.append(geo)
                time.sleep(1.1)

        # write results into an xml file
        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        path_loc_xml = os.path.join(self.path, 'geocodes.xml')
        with open(path_loc_xml, 'w') as output_file:
            output_file.write(str)

        # loc = self.geolocator.geocode(name)
        # if loc is not None:
        #     # location = '%s %f %f \n' % (loc[0].encode('utf-8'), loc.latitude, loc.longitude)
        #     return loc.latitude, loc.longitude
        #     #with codecs.open('/var/data/nlp/presse_subset/sub_locations.txt', 'a') as output:
        #     #    output.write(location)
        # return '', ''



class testGeocoder(unittest.TestCase):

    def testGeocoding(self):
        Geocoder('path/to/locations.txt')

        # root = L.geocodes({})

        # with codecs.open('/var/data/nlp/presse_subset/clean_locations.txt', 'r') as input:
        #     for entity in input.readlines():
        #         entity.strip('\n')
        #         print 'Nominatim call for: %s' % entity
        #         lat, long = coords.get_coordinates(entity)
        #         geo = L.georesult({'name': entity.decode('utf-8'),
        #                            'latitude': lat,
        #                            'longitude': long,
        #                            'idf': ''})
        #         root.append(geo)
        #         time.sleep(1.1)
        #
        #     str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        #     path_loc_xml = os.path.join('/var/data/nlp/presse_subset/', 'geocodes.xml')
        #     with open(path_loc_xml, 'w') as output_file:
        #         output_file.write(str)


if __name__ == '__main__':
    unittest.main()