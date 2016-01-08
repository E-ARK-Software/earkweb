import os
import unittest
from nltk.tag import StanfordNERTagger
import codecs
from lxml import etree, objectify
from collections import Counter

L = objectify.ElementMaker(
    annotate=False)

class NETagger(object):
    def __init__(self, path):
        model = '/opt/Projects/nlp/stanford-ner-2015-04-20/classifiers/german/german.hgc_175m_600.crf.ser.gz'
        jar = '/opt/Projects/nlp/stanford-ner-2015-04-20/stanford-ner.jar'

        self.tagger = StanfordNERTagger(model, jar, encoding='utf-8', java_options='-mx8000m')
        self.path = path

    def assign_tags(self, file):
        with open(file, 'r') as f:
            tokens = f.readlines()
            ne_result = self.tagger.tag(tokens)

        root = L.locations({'file': file,
                            'tokens': len(tokens).__str__()})

        locations = []
        position = 0
        frequency = Counter(tokens)

        # TODO: sort out the '\n' in all the documents/lists... also for the other scripts!

        for entity, tag in ne_result:
            position += 1
            if tag == 'I-LOC':
                locations.append(entity.encode('utf-8'))
                # add to xml
                loc = L.location({'name': entity,
                                  'latitude': '',
                                  'longitude': '',
                                  'position': position,
                                  'tf': frequency['%s\n' % entity.encode('utf-8')].__str__(), # TODO: \n
                                  'tfidf': ''})
                root.append(loc)

        # create the xml file - keep connection between source file and locations
        str = etree.tostring(root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        filename = os.path.basename(file)
        path_loc_xml = os.path.join(self.path, 'ner/%s.xml' % filename)
        with open(path_loc_xml, 'w') as output_file:
            output_file.write(str)

        # one central file with all locations - needed for geocoding
        with codecs.open(os.path.join(self.path, 'locations.txt'), 'a', 'utf-8') as output:
            for name in list(set(locations)):
                # This ensures the following: if in the central file a name is duplicated, it means that it shows up
                # in more than one source file. Number of occurrences = number of files (newspaper issues) that
                # contain this word. This information is needed to calculate the tf-idf.
                output.write('%s\n' % name.decode('utf-8'))
            print 'Extracted locations for %s ...' % file

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



class testNETagger(unittest.TestCase):

    def testTagging(self):
        tagger = NETagger('/var/data/nlp/presse_subset/')

        for file in os.listdir('/var/data/nlp/presse_subset/ner'):
            tagger.assign_tags('/var/data/nlp/presse_subset/ner/%s' % file)

        # tagger.removeDuplicates()

        # tagger.assign_tags('/var/data/nlp/presse_subset/ner/18751023_tokenized')


if __name__ == '__main__':
    unittest.main()