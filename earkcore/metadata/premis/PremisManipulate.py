from lxml import etree, objectify
from datetime import datetime
from earkcore.metadata.XmlHelper import q, XSI_NS, sequence_insert
from earkcore.utils.xmlutils import pretty_xml_string
from earkcore.xml.xmlvalidation import XmlValidation
import unittest


PREMIS_NS = 'info:lc/xmlns/premis-v2'
PREMIS_NSMAP = {None: PREMIS_NS}
P = objectify.ElementMaker(
    annotate=False,
    namespace=PREMIS_NS,
    nsmap=PREMIS_NSMAP)


class Premis:

    premis_successor_sections = ['object', 'event', 'agent', 'right']

    def __init__(self, f=None):
        self.root = objectify.parse(f).getroot()

    def add_object(self, identifier_value):
        sequence_insert(
            self.root, P.object(
                {q(XSI_NS, 'type'): 'file'},
                P.objectIdentifier(
                    P.objectIdentifierType('FILEPATH'),
                    P.objectIdentifierValue(identifier_value)
                ),
                P.objectCharacteristics(
                    P.compositionLevel(0),
                    P.format(
                        P.formatRegistry(
                            P.formatRegistryName,
                            P.formatRegistryKey
                        )
                    )
                )
            ),
            self.premis_successor_sections
        )

    def add_event(self, identifier_value, agent):
        sequence_insert(
            self.root, P.event(
                P.eventIdentifier(
                    P.eventIdentifierType('LOCAL'),
                    P.eventIdentifierValue(identifier_value)
                ),
                P.eventType,
                P.eventDateTime(datetime.utcnow().isoformat()),
                P.linkingAgentIdentifier(
                    P.linkingAgentIdentifierType('LOCAL'),
                    P.linkingAgentIdentifierValue(agent)
                )
            ),
            self.premis_successor_sections
        )

    def add_agent(self, identifier_value):
        sequence_insert(
            self.root, P.agent(
                P.agentIdentifier(
                    P.agentIdentifierType('LOCAL'),
                    P.agentIdentifierValue(identifier_value)
                ),
                P.agentName('E-ARK AIP to DIP Converter'),
                P.agentType('Software')
            ),
            self.premis_successor_sections
        )

    def __str__(self):
        return etree.tostring(self.root, encoding='UTF-8', pretty_print=False, xml_declaration=True)

    def to_string(self):
        return self.__str__()


class TestTaskLogger(unittest.TestCase):

    with open('../../../earkresources/PREMIS_skeleton.xml', 'r') as premis_file:
        my_premis = Premis(premis_file)

    def test_log(self):

        self.my_premis.add_agent('Aip2Dip')
        self.my_premis.add_event('Migration01', 'Aip2Dip')
        self.my_premis.add_object('file.txt')
        premis_xml = pretty_xml_string(self.my_premis.to_string())
        print premis_xml

        xmlval = XmlValidation()
        parsed_xml = etree.fromstring(premis_xml)
        parsed_schema = etree.parse('../../../earkresources/schemas/premis-v2-2.xsd')
        validation_result = xmlval.validate_XML(parsed_xml,parsed_schema)
        if len(validation_result.err) > 0:
            print validation_result.err
        self.assertTrue(validation_result.valid)

if __name__ == '__main__':
    unittest.main()
