__author__ = 'jan'

from lxml import etree

def MetaIdentification(unknown_xml):
    parsed_unknown = etree.parse(unknown_xml)
    unknown_tag =  parsed_unknown.getroot().tag
    tag = unknown_tag.split('}')
    if len(tag) == 2:
        return tag[1]
    elif len(tag) == 1:
        return tag[0]



def main():
    # identification_result = MetaIdentification('/var/data/earkweb/reception/DNA_AVID.SA.18001.01_141104/Metadata/pitt-mss297.xml')
    identification_result = MetaIdentification('/var/data/earkweb/reception/DNA_AVID.SA.18001.01_141104/Metadata/tableIndex.xml')

    print 'xml file identified as: ' + identification_result

if __name__ == '__main__':
    main()

