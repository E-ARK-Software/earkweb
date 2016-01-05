import os
import unittest
import codecs
from lxml import etree
from collections import Counter
import math

class EntityStatistics(object):

    def __init__(self):
        pass

    def idf(self):
        # calculate inverse document frequency (idf) for every entity in geocodes.xml
        # idf(term, corpus) = log10(<number of documents in corpus> / <number of documents that contain term>)
        locs = etree.parse('/var/data/nlp/presse_subset/geocodes.xml').getroot()

        with open('/var/data/nlp/presse_subset/locations.txt', 'r') as input:
            namelist = input.readlines()
            frequency = Counter(namelist) # ({'Wien': 12, 'Budweis': 7}) - number of documents this entity occurred in
            for location in locs.getchildren():
                # find out how often the entities name occurs and get the idf value
                # TODO: for this subset, we have 50 issues, so this is hardcoded
                idf = math.log10(50/frequency[location.attrib['name'].encode('utf-8')])
                location.set('idf', idf.__str__())

        str = etree.tostring(locs, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        with open('/var/data/nlp/presse_subset/geocodes.xml', 'w') as output:
            output.write(str)

    def tfidf(self):
        # calculate tf-idf for the entities of each newspaper issue
        geocoded_locs = etree.parse('/var/data/nlp/presse_subset/geocodes.xml')

        for file in os.listdir('/var/data/nlp/presse_subset/tokens'):
            if file.endswith('.xml'):
                entities = etree.parse('/var/data/nlp/presse_subset/tokens/%s' % file).getroot()
                for entity in entities.getchildren():
                    # find the geocoded entity
                    geo = geocoded_locs.find('//georesult[@name="%s\n"]' % entity.attrib['name']) # TODO: \n problem
                    entity.set('tfidf', (float(entity.attrib['tf'])*float(geo.attrib['idf'])).__str__())
                    # copy coordinates
                    entity.set('longitude', geo.attrib['longitude'])
                    entity.set('latitude', geo.attrib['latitude'])

                # write updated entries to file
                str = etree.tostring(entities, encoding='UTF-8', pretty_print=True, xml_declaration=True)
                with open('/var/data/nlp/presse_subset/tokens/%s' % file, 'w') as output:
                    output.write(str)



class testEntityStatistics(unittest.TestCase):

    def testTfidf(self):
        stats = EntityStatistics()
        # stats.idf()
        stats.tfidf()


if __name__ == '__main__':
    unittest.main()