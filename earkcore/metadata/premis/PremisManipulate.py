from lxml import etree, objectify
from datetime import datetime

PREMIS_NS = 'info:lc/xmlns/premis-v2'
PREMIS_NSMAP = {None: PREMIS_NS}
P = objectify.ElementMaker(
    annotate=False,
    namespace=PREMIS_NS,
    nsmap=PREMIS_NSMAP)


class Premis:

    def __init__(self, f=None):
        self.root = objectify.parse(f).getroot()

    def add_event(self, identifier_value):
        self.root.agent.addprevious(
            P.event(
                P.eventIdentifier(
                    P.eventIdentifierType,
                    P.eventIdentifierValue(identifier_value)
                ),
                P.eventType,
                P.eventDateTime(datetime.utcnow().isoformat())
            )
        )

    def validate(self):
        with open('../../Downloads/premis.xsd', 'r') as f:
            xmlschema = etree.XMLSchema(file=f)
        return xmlschema.validate(self.root)

    def __str__(self):
        return etree.tostring(self.root, encoding='UTF-8', pretty_print=True, xml_declaration=True)


def main():
    with open('earkresources/AIP-test/AIP-compound/aip-metadata/PREMIS.xml', 'r') as premis_file:
        my_premis = Premis(premis_file)
    my_premis.add_event('Migration01')
    print my_premis
    print my_premis.validate()

if __name__ == "__main__":
    main()
