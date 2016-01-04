import json
import os
import unittest
import nltk
import codecs


class JsonDecoder(object):
    def __init__(self, source):
        self.newspaper_location = os.path.join('/var/data/nlp/', source)
        self.newspaper_list = os.listdir(self.newspaper_location)

    def decode(self):
        for issue in self.newspaper_list:
            # if issue == 'tokens': self.newspaper_list.pop(self.newspaper_list.index(issue))
            issue_json = os.listdir(os.path.join(self.newspaper_location, issue))[0]
            with open(os.path.join(self.newspaper_location, issue, issue_json), 'r') as f:
                json_obj = json.load(f)
                for entity in json_obj['contentAsText']:
                    tokenized_text = ''
                    for token in nltk.word_tokenize(entity, language='german'):
                        tokenized_text += ('%s\n' % token)
                        if token in '!?.':
                            tokenized_text += '\n'
                    with codecs.open(os.path.join(self.newspaper_location, 'tokens/%s_tokenized' % issue), 'w',
                                     'utf-8') as output:
                        tokenized_text.encode('utf-8')
                        output.write(tokenized_text)
                print 'Tokenized file: %s ...' % issue_json


class TestJsonDecoder(unittest.TestCase):

    def test_decoding(self):
        decoder = JsonDecoder('presse_subset')
        decoder.decode()


if __name__ == '__main__':
    unittest.main()

