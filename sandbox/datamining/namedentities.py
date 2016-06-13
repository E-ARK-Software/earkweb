import os
import unittest
from nltk.tag import StanfordNERTagger
from lxml import etree, objectify
from nltk import word_tokenize
from helpers.existwriter import write_to_exist

E = objectify.ElementMaker(
    annotate=False)


class NERecogniser(object):
    # TODO: add geo-referencing

    def __init__(self, path, model):
        # model = '/opt/Projects/nlp/stanford-ner-2015-04-20/classifiers/german/german.hgc_175m_600.crf.ser.gz'
        jar = '/opt/Projects/nlp/stanford-ner-2015-04-20/stanford-ner.jar'

        self.tagger = StanfordNERTagger(model, jar, encoding='utf-8', java_options='-mx8000m')
        self.path = path

    def assign_tags(self, content, identifier):
        # starttime = time.time()

        tokenized = []
        content = content.strip().decode('utf-8')
        tokens = word_tokenize(content, language='english')
        for token in tokens:
            tokenized.append(token + '\n')

        root = E.entities({'file': identifier,
                           'tokens': len(tokenized).__str__()})

        position = 0
        for result in self.tagger.tag(tokenized):
            position += 1
            if result[1] != 'O':
                entity = E.entity({'position': position,
                                   'class': result[1],
                                   'entity': result[0]})
                root.append(entity)

        xml_string = etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True)

        exist_db = write_to_exist(xml_string, identifier)

        return 0 if exist_db in (200, 201) else 1


    # def removeDuplicates(self):
    #     names_no_duplicates = ''
    #     with codecs.open(os.path.join(self.path, 'locations.txt'), 'rw') as loc:
    #         all_names = loc.readlines()
    #         # remove all entries that appear more than once - to avoid superfluous geocoder API calls
    #         for name in list(set(all_names)):
    #             names_no_duplicates += name
    #
    #     with codecs.open(os.path.join(self.path, 'clean_locations.txt'), 'w') as output:
    #         for name in names_no_duplicates:
    #             output.write(name)


# class testNETagger(unittest.TestCase):
#
#     def testTagging(self):
#         tagger = NERecogniser('/var/data/nlp/presse_subset/')
#
#         for filename in os.listdir('/var/data/nlp/presse_subset/ner'):
#             tagger.assign_tags('/var/data/nlp/presse_subset/ner/%s' % filename)
#
#         # tagger.removeDuplicates()
#
#         # tagger.assign_tags('/var/data/nlp/presse_subset/ner/18751023_tokenized')
#
#
# if __name__ == '__main__':
#     unittest.main()
