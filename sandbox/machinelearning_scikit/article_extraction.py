import os
from lxml import etree

class ArticleExtraction(object):
    def __init__(self, source, target):
        self.raw_data_path = source
        self.extracted_data_path = target

    def from_xml(self):
        counter = 0
        for file in os.listdir(self.raw_data_path):
            # root = etree.parse(os.path.join(self.raw_data_path, file)).getroot()
            for event, element in etree.iterparse(os.path.join(self.raw_data_path, file)):
                if element.tag == 'doc':
                    category = ''
                    article = ''
                    # every <doc> contains one article
                    for child in element.getchildren():
                        if child.attrib['name'] == 'category':
                            # use article category for categorization
                            category = child.text.split(' ')[0]
                            if not os.path.exists(os.path.join(self.extracted_data_path, category)):
                                # create a folder for all articles with the same category
                                os.mkdir(os.path.join(self.extracted_data_path, category))
                        if child.attrib['name'] == 'articleBody':
                            article = child.text
                            counter += 1
                    # print 'Would write to: %s' % os.path.join(self.extracted_data_path, category, '%s.txt' % str(counter).zfill(4))
                    with open(os.path.join(self.extracted_data_path, category, '%s.txt' % str(counter).zfill(4)), 'w') as output:
                        output.write(article.encode('utf-8'))
                else:
                    pass

if __name__ == '__main__':
    source = '/var/data/earkweb/machinelearning/raw'
    target = '/home/janrn/Development/machinelearning/articles'
    extractor = ArticleExtraction(source, target)
    extractor.from_xml()
