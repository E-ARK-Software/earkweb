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

    def addObject(self):
        # file + path
        # mandatory things
        # related object: if this file was migrated, link prior version
        pass

    def addEvent(self, premispath, info):
        pass

    def createMigrationPremis(self, premis_info):
        PREMIS_ATTRIBUTES = {"version" : "2.0"}
        premis = P.premis(PREMIS_ATTRIBUTES)
        premis.attrib['{%s}schemaLocation' % XSI_NS] = "info:lc/xmlns/premis-v2 ../../schemas/premis-v2-2.xsd"

        # add agent
        identifier_value = 'earkweb'
        premis.append(P.agent(
                P.agentIdentifier(
                    P.agentIdentifierType('LOCAL'),
                    P.agentIdentifierValue(identifier_value)
                ),
                P.agentName('E-ARK AIP to DIP Converter'),
                P.agentType('Software')))

        migrations = etree.iterparse(open(premis_info['info']), events=('start',))
        for event, element in migrations:
            if element.tag == 'migration':
                event_id = uuid.uuid4().__str__()
                if self.root_path.endswith(element.attrib['targetrep']):
                    linked_object = os.path.relpath(os.path.join(element.attrib['sourcedir'], element.attrib['file']), self.root_path)

                    event = P.event(
                        P.eventIdentifier(
                            P.eventIdentifierType('local'),
                            P.eventIdentifierValue(event_id)),
                        P.eventType,
                        P.eventDateTime(current_timestamp()),
                        P.linkingAgentIdentifier(
                            P.linkingAgentIdentifierType('local'),
                            P.linkingAgentIdentifierValue('should probably come from migrations.xml')),
                        P.linkingObjectIdentifier(
                            P.linkingObjectIdentifierType('local'),
                            P.linkingObjectIdentifierValue(linked_object))
                    )
                    premis.append(event)
                else:
                    pass
            else:
                pass

        # create the Premis file
        str = etree.tostring(premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        preservation_dir = os.path.join(self.root_path, './metadata/preservation')
        if not os.path.exists(preservation_dir):
            os.mkdir(preservation_dir)
        path_premis = os.path.join(self.root_path, './metadata/preservation/premis.xml')
        with open(path_premis, 'w') as output_file:
            output_file.write(str)

        # if the object is a migration/representation:
                # # create the event,
                # # link the event to this object,
                # # link the corresponding object in prior representation
                # if premis_info is not None:
                #     if premis_info['event'] == 'migration':
                #         source = premis_info['source']
                #
                #
                #
                #         # related_object = '/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/submission/representations/%s/data/%s' % (source, nm)
                #         # related_object_path = os.path.relpath('/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/submission/representations/%s/data/%s' % (source, nm), self.root_path)
                #         # # print related_object_path
                #         # rel_object = P.relatedObjectIdentification(
                #         #     P.relatedObjectIdentifierType('local'),
                #         #     P.relatedObjectIdentifierValue('migration source'),
                #         #     P.relatedObjectIdentifierSequence('not applicable')
                #         # )
                #         # object.append(rel_object)
                # else:
                #     pass

    def createPremis(self, enable_jhove = False):
        jhove_parser = None
        if enable_jhove == True:
            jhove_parser = etree.XMLParser(remove_blank_text=True)

        PREMIS_ATTRIBUTES = {"version" : "2.0"}
        premis = P.premis(PREMIS_ATTRIBUTES)
        premis.attrib['{%s}schemaLocation' % XSI_NS] = "info:lc/xmlns/premis-v2 ../../schemas/premis-v2-2.xsd"

        # add agent
        identifier_value = 'earkweb'
        premis.append(P.agent(
                P.agentIdentifier(
                    P.agentIdentifierType('LOCAL'),
                    P.agentIdentifierValue(identifier_value)
                ),
                P.agentName('E-ARK AIP to DIP Converter'),
                P.agentType('Software')))

        # premis_ids = []
        # create premis objects for files in this representation (self.root_path)
        for top, dirs, files in os.walk(os.path.join(self.root_path, 'data')):
            for nm in files:
                file_name = os.path.join(top,nm)
                hash = self.sha256(file_name)
                file_url = "file://./%s" % os.path.relpath(file_name, self.root_path)
                fmt = self.fid.identify_file(file_name)#os.path.abspath(remove_protocol(file_url)))
                jhove = None
                if enable_jhove == True:
                    try:
                        result = self.runCommand(["/usr/bin/jhove", "-h", "xml", file_name] )
                        if result[0] == 0:
                            jhove = etree.XML(result[1], parser=jhove_parser)
                    except Exception:
                        #TODO: handle exception
                        pass

                size = os.path.getsize(file_name)
                premis_id = uuid.uuid4()
                # premis_ids.append(premis_id)

                # create a Premis object
                object = P.object(
                        {q(XSI_NS, 'type'): 'file', "xmlID":premis_id},
                        P.objectIdentifier(
                            P.objectIdentifierType('LOCAL'),
                            P.objectIdentifierValue(premis_id)
                        ),
                        P.objectIdentifier(
                            P.objectIdentifierType('FILEPATH'),
                            P.objectIdentifierValue(file_url)
                        ),
                        P.objectCharacteristics(
                            P.compositionLevel(0),
                            P.size(size),
                            P.fixity(
                                P.messageDigestAlgorithm("SHA-256"),
                                P.messageDigest(hash),
                                P.messageDigestOriginator("hashlib")
                            ),
                            P.format(
                                P.formatRegistry(
                                    P.formatRegistryName("PRONOM"),
                                    P.formatRegistryKey(fmt),
                                    P.formatRegistryRole("identification")
                                )
                            ),
                            #P.objectCharacteristicsExtension(
                                #TODO:// generate id or reference from somewhere
                            #    P.mdSec({"ID":"ID426087e8-0f79-11e3-847a-34e6d700c47b"},
                            #        P.mdWrap({"MDTYPE":"OTHER", "OTHERMDTYPE":"JHOVE"},
                            #            P.xmlData(
                            #                jhove
                            #                 )
                            #                 )
                            #)
                        ),
                    )
                # append Premis object to premis root
                premis.append(object)

        # event
        identifier_value = 'AIP Creation'
        linking_agent = 'earkweb'
        linking_object=None
        premis.append(P.event(
                P.eventIdentifier(
                    P.eventIdentifierType('LOCAL'),
                    P.eventIdentifierValue(identifier_value)
                ),
                P.eventType,
                P.eventDateTime(current_timestamp()),
                P.linkingAgentIdentifier(
                    P.linkingAgentIdentifierType('LOCAL'),
                    P.linkingAgentIdentifierValue(linking_agent)
                ),

                P.linkingAgentIdentifier(
                    P.linkingAgentIdentifierType('LOCAL'),
                    P.linkingAgentIdentifierValue(linking_object)
                )
                if linking_object is not None else None
            ))

        str = etree.tostring(premis, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        preservation_dir = os.path.join(self.root_path, './metadata/preservation')
        if not os.path.exists(preservation_dir):
            os.mkdir(preservation_dir)
        path_premis = os.path.join(self.root_path, './metadata/preservation/premis.xml')
        with open(path_premis, 'w') as output_file:
            output_file.write(str)

        # return premis_ids
        return

class testPremisCreation(unittest.TestCase):
    def testCreatePremis(self):
        # premisgen = PremisGenerator(os.path.join("/var/data/earkweb/work/bbfc7446-d2af-4ab9-8479-692c270989bb"))
        premisgen = PremisGenerator("/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/representations/rep-1_mig-1")
        # mets_data = {'packageid': '996ed635-3e13-4ee5-8e5b-e9661e1d9a93',
        #              'type': 'AIP'}
        #premis_info = None
        premis_info = {'event': 'migration',
                       'info': '/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b/metadata/earkweb/migrations.xml',
                       'source': 'rep-1'}
        premisgen.createMigrationPremis(premis_info)

    # def testAddEvent(self):
    #     premisgen = PremisGenerator("/var/data/earkweb/work/c214c594-421d-4026-81b1-d71250eb826b")
    #     info = {'time': current_timestamp(),
    #             'eventidtype': 'migration',
    #             'agenttype': 'program',
    #             'agentvalue': 'Ghostscript 9.18',
    #             'outcome': 'SUCCESS',
    #             'objectvalue': 'file created through migration',
    #             'relatedobject': 'file that was migrated',
    #             'eventtype': 'migration',
    #             'eventdetail': 'command line parameters'
    #             }
    #     print premisgen.addEvent('representations/rep-1_mig-1/metadata/preservation/premis.xml', info)


if __name__ == '__main__':
    unittest.main()