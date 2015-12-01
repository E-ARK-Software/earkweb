import os

from lxml import etree, objectify
import unittest
import hashlib
import uuid
from mimetypes import MimeTypes

from config.config import root_dir
from subprocess import Popen, PIPE
from earkcore.utils.datetimeutils import current_timestamp, DT_ISO_FMT_SEC_PREC, get_file_ctime_iso_date_str

from earkcore.format.formatidentification import FormatIdentification
from earkcore.metadata.XmlHelper import q, XSI_NS

PREMIS_NS = 'info:lc/xmlns/premis-v2'
PREMIS_NSMAP = {None: PREMIS_NS}

P = objectify.ElementMaker(
    annotate=False,
    namespace=PREMIS_NS,
    nsmap=PREMIS_NSMAP)

class PremisGenerator(object):
    fid = FormatIdentification()
    mime = MimeTypes()
    root_path = ""

    def __init__(self, root_path):
        print "Working in rootdir %s" % root_path
        self.root_path = root_path

    def sha256(self, fname):
        hash = hashlib.sha256()
        with open(fname) as f:
            for chunk in iter(lambda: f.read(4096), ""):
                hash.update(chunk)
        return hash.hexdigest()

    def runCommand(self, program, stdin = PIPE, stdout = PIPE, stderr = PIPE):
        result, res_stdout, res_stderr = None, None, None
        try:
            # quote the executable otherwise we run into troubles
            # when the path contains spaces and additional arguments
            # are presented as well.
            # special: invoking bash as login shell here with
            # an unquoted command does not execute /etc/profile

            print 'Launching: '+ ' '.join(program)
            process = Popen( program, stdin = stdin, stdout = stdout, stderr = stderr, shell = False)

            res_stdout, res_stderr = process.communicate()
            result = process.returncode
            print 'Finished: '+ ' '.join(program)

        except Exception as ex:
            res_stderr = ''.join(str(ex.args))
            result = 1

        if result != 0:
            print 'Command failed:' + ''.join(res_stderr)
            raise Exception('Command failed:' + ''.join(res_stderr))

        return result, res_stdout, res_stderr

    def addObject(self, abs_path):
        '''
        Must be called with the absolute path to a file.

        @param abs_path:    absolute file path
        @return:            Premis object
        '''

        hash = self.sha256(abs_path)
        file_url = "file://./%s" % os.path.relpath(abs_path, self.root_path)
        fmt = self.fid.identify_file(abs_path)
        size = os.path.getsize(abs_path)
        premis_id = 'ID' + uuid.uuid4().__str__()

        # create a Premis object
        object = P.object(
            {q(XSI_NS, 'type'): 'file', "xmlID": premis_id},
            P.objectIdentifier(
                P.objectIdentifierType('filepath'),
                P.objectIdentifierValue(file_url)
            ),
            P.objectCharacteristics(
                P.compositionLevel(0),
                P.fixity(
                    P.messageDigestAlgorithm("SHA-256"),
                    P.messageDigest(hash),
                    P.messageDigestOriginator("hashlib")
                ),
                P.size(size),
                P.format(
                    P.formatRegistry(
                        P.formatRegistryName("PRONOM"),
                        P.formatRegistryKey(fmt),
                        P.formatRegistryRole("identification")
                    )
                ),
            ),
        )
        return object

    def addEvent(self, premispath, info):
        '''
        Add an event to an exisiting Premis file (DefaultTask finalize method).

        @param premispath:
        @param info:
        @return:
        '''
        # print type(premispath)

        outcome = info['outcome']
        agent = info['task_name']
        event_type = info['event_type']
        linked_object = info['linked_object']

        premis_path = os.path.join(self.root_path, premispath)
        premis_parsed = etree.parse(premis_path)
        premis_root = premis_parsed.getroot()

        event_id = 'ID' + uuid.uuid4().__str__()
        event = P.event(
            P.eventIdentifier(
                P.eventIdentifierType('local'),
                P.eventIdentifierValue(event_id)),
            P.eventType(event_type),
            P.eventDateTime(current_timestamp()),
            P.eventOutcomeInformation(
                P.eventOutcome(outcome)
            ),
            P.linkingAgentIdentifier(
                P.linkingAgentIdentifierType('software'),
                P.linkingAgentIdentifierValue(agent)),
            P.linkingObjectIdentifier(
                P.linkingObjectIdentifierType('repository'),
                P.linkingObjectIdentifierValue(linked_object))
        )
        premis_root.insert(len(premis_root) - 1, event)

        str = etree.tostring(premis_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        with open(premis_path, 'w') as output_file:
            output_file.write(str)

        return

    def createMigrationPremis(self, premis_info):
        PREMIS_ATTRIBUTES = {"version" : "2.0"}
        premis = P.premis(PREMIS_ATTRIBUTES)
        premis.attrib['{%s}schemaLocation' % XSI_NS] = "info:lc/xmlns/premis-v2 ../../schemas/premis-v2-2.xsd"

        # creates an object that references the package or representation
        # TODO: identifier!
        premis_id = 'ID' + uuid.uuid4().__str__()
        object = P.object(
            {q(XSI_NS, 'type'): 'representation', "xmlID": premis_id},
            P.objectIdentifier(
                P.objectIdentifierType('repository'),
                P.objectIdentifierValue('package-id-goes-here-?')
            ),
        )
        premis.append(object)

        # parse the migration.xml, add events and objects
        migrations = etree.iterparse(open(premis_info['info']), events=('start',))
        eventlist = []
        for event, element in migrations:
            if element.tag == 'migration':
                event_id = 'ID' + uuid.uuid4().__str__()
                if self.root_path.endswith(element.attrib['targetrep']):
                    source_object_abs = os.path.join(element.attrib['sourcedir'], element.attrib['file'])
                    source_object_rel = "file://./%s" % os.path.relpath(source_object_abs, self.root_path)
                    target_object_abs = os.path.join(element.attrib['targetdir'], element.attrib['output'])
                    target_object_rel = "file://./%s" % os.path.relpath(target_object_abs, self.root_path)

                    # event
                    event = P.event(
                        P.eventIdentifier(
                            P.eventIdentifierType('local'),
                            P.eventIdentifierValue(event_id)),
                        P.eventType('migration'),
                        P.eventDateTime(element.attrib['starttime']), # TODO: use event start or event end time?
                        P.eventOutcomeInformation(
                            P.eventOutcome('success')
                        ),
                        P.linkingAgentIdentifier(
                            P.linkingAgentIdentifierType('software'),
                            P.linkingAgentIdentifierValue('should probably come from migrations.xml')),
                        P.linkingObjectIdentifier(
                            P.linkingObjectIdentifierType('filepath'),
                            P.linkingObjectIdentifierValue(target_object_rel))
                    )
                    eventlist.append(event)

                    # object
                    object = self.addObject(target_object_abs)
                    # add the relationship to the migration event and the source file
                    relationship = P.relationship(
                        P.relationshipType('derivation'),
                        P.relationshipSubType('has source'),
                        P.relatedObjectIdentification(
                            P.relatedObjectIdentifierType('filepath'),
                            P.relatedObjectIdentifierValue(source_object_rel),
                            P.relatedObjectSequence('0')
                        ),
                        P.relatedEventIdentification(
                            P.relatedEventIdentifierType('local'),
                            P.relatedEventIdentifierValue(event_id),
                            P.relatedEventSequence('1')
                        ),
                    )
                    object.append(relationship)

                    premis.append(object)
                else:
                    pass
            else:
                pass

        # append all events to premis root - they must be below the objects (due to validation)
        for event in eventlist:
            premis.append(event)

        # add agent
        identifier_value = 'earkweb'
        premis.append(P.agent(
                P.agentIdentifier(
                    P.agentIdentifierType('LOCAL'),
                    P.agentIdentifierValue(identifier_value)
                ),
                P.agentName('E-ARK AIP to DIP Converter'),
                P.agentType('Software')))

        # create the Premis file
        str = etree.tostring(premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        preservation_dir = os.path.join(self.root_path, 'metadata/preservation')
        if not os.path.exists(preservation_dir):
            os.makedirs(preservation_dir)
        path_premis = os.path.join(self.root_path, 'metadata/preservation/premis.xml')
        with open(path_premis, 'w') as output_file:
            output_file.write(str)

        return


    def createPremis(self):
        PREMIS_ATTRIBUTES = {"version" : "2.0"}
        premis = P.premis(PREMIS_ATTRIBUTES)
        premis.attrib['{%s}schemaLocation' % XSI_NS] = "info:lc/xmlns/premis-v2 ../../schemas/premis-v2-2.xsd"

        # if there are no /data files, this will ensure that there is at least one object (the IP itself)
        premis_id = 'ID' + uuid.uuid4().__str__()
        object = P.object(
            {q(XSI_NS, 'type'): 'representation', "xmlID": premis_id},
            P.objectIdentifier(
                P.objectIdentifierType('repository'),
                P.objectIdentifierValue('package-id-goes-here-?')
            ),
        )
        premis.append(object)

        # create premis objects for files in this representation (self.root_path/data)
        for directory, subdirectories, filenames in os.walk(os.path.join(self.root_path, 'data')):
            for filename in filenames:
                object = self.addObject(os.path.join(directory, filename))
                premis.append(object)

        # # event
        # identifier_value = 'AIP Creation'
        # linking_agent = 'earkweb'
        # linking_object=None
        # premis.append(P.event(
        #         P.eventIdentifier(
        #             P.eventIdentifierType('local'),
        #             P.eventIdentifierValue(identifier_value)
        #         ),
        #         P.eventType,
        #         P.eventDateTime(current_timestamp()),
        #         P.linkingAgentIdentifier(
        #             P.linkingAgentIdentifierType('local'),
        #             P.linkingAgentIdentifierValue(linking_agent)
        #         ),
        #
        #         P.linkingAgentIdentifier(
        #             P.linkingAgentIdentifierType('local'),
        #             P.linkingAgentIdentifierValue(linking_object)
        #         )
        #         if linking_object is not None else None
        #     ))

        # add agent
        identifier_value = 'earkweb'
        premis.append(P.agent(
            P.agentIdentifier(
                P.agentIdentifierType('LOCAL'),
                P.agentIdentifierValue(identifier_value)
            ),
            P.agentName('E-ARK AIP to DIP Converter'),
            P.agentType('Software')))

        str = etree.tostring(premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        preservation_dir = os.path.join(self.root_path, './metadata/preservation')
        if not os.path.exists(preservation_dir):
            os.mkdir(preservation_dir)
        path_premis = os.path.join(self.root_path, './metadata/preservation/premis.xml')
        with open(path_premis, 'w') as output_file:
            output_file.write(str)

        return

from config import config
class testPremisCreation(unittest.TestCase):
    def validateThis(self, file):
        validation_errors = []
        xmlschema = etree.XMLSchema(etree.parse(config.premis_schema_file))
        try:
            xmlschema.assertValid(etree.parse(file))
            print 'Validation result: %s' % xmlschema.validate(etree.parse(file))
        except etree.XMLSyntaxError, e:
            validation_errors.append(e.error_log)
        if len(validation_errors) > 0:
            print validation_errors

    # def testCreatePremis(self):
    #     premisgen = PremisGenerator("/var/data/earkweb/work/0708258c-7e91-42fe-a91a-08b63c66c315")
    #     premisgen.createPremis()
    #     self.validateThis('/var/data/earkweb/work/0708258c-7e91-42fe-a91a-08b63c66c315/metadata/preservation/premis.xml')

    # def testCreateMigrationPremis(self):
    #     premisgen = PremisGenerator("/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/representations/rep-1_mig-1")
    #     premis_info = {'info': '/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/metadata/earkweb/migrations.xml'}
    #     premisgen.createMigrationPremis(premis_info)
    #
    #     premis = '/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/representations/rep-1_mig-1/metadata/preservation/premis.xml'
    #     self.validateThis(premis)

    def testAddEvent(self):
        premisgen = PremisGenerator("/var/data/earkweb/work/0708258c-7e91-42fe-a91a-08b63c66c315")

        premisinfo = {'outcome': 'success',
                      'task_name': 'SIPValidation',
                      'event_type': 'SIP validation',
                      'linked_object': 'this-is-a-package-id'}

        premisgen.addEvent('metadata/preservation/premis.xml', premisinfo)
        self.validateThis('/var/data/earkweb/work/0708258c-7e91-42fe-a91a-08b63c66c315/metadata/preservation/premis.xml')




if __name__ == '__main__':
    unittest.main()