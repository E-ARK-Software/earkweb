from lxml import etree, objectify
from datetime import datetime
from earkcore.metadata.XmlHelper import q, XSI_NS

PREMIS_NS = 'info:lc/xmlns/premis-v2'
PREMIS_NSMAP = {None: PREMIS_NS}
P = objectify.ElementMaker(
    annotate=False,
    namespace=PREMIS_NS,
    nsmap=PREMIS_NSMAP)


class Premis:

    def __init__(self, f=None):
        self.root = objectify.parse(f).getroot()

    def add_object(self, identifier_value):
        self.root.event.addprevious(
            P.object(
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
            )
        )

    def add_event(self, identifier_value, agent):
        self.root.agent.addprevious(
            P.event(
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
            )
        )

    def add_agent(self, identifier_value):
        self.root.rights.addprevious(
            P.agent(
                P.agentIdentifier(
                    P.agentIdentifierType('LOCAL'),
                    P.agentIdentifierValue(identifier_value)
                ),
                P.agentName('E-ARK AIP to DIP Converter'),
                P.agentType('Software')
            )
        )

    def validate(self):
        with open('../../Downloads/premis.xsd', 'r') as f:
            xmlschema = etree.XMLSchema(file=f)
        return xmlschema.validate(self.root)

    def __str__(self):
        return etree.tostring(self.root, encoding='UTF-8', pretty_print=True, xml_declaration=True)

    def to_string(self):
        return self.__str__()


def main():
    with open('earkresources/AIP-test/AIP-compound/aip-metadata/PREMIS.xml', 'r') as premis_file:
        my_premis = Premis(premis_file)
    my_premis.add_object('file.txt')
    my_premis.add_agent('Aip2Dip')
    my_premis.add_event('Migration01', 'Aip2Dip')
    print my_premis
    print my_premis.validate()

if __name__ == "__main__":
    main()
