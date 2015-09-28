from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree as Etree
from earkcore.utils.xmlutils import prettify
from workers.taskconfig import TaskConfig


class TaskExecutionXml(object):
    """
    TaskExecutionXml class which represents an XML document to persist task execution parameters and results.
    The class can be initiated by parameters (static method from_parameters), by XML content string (static
    method from_content), or by an XML file path (static method from_path). Furthermore, it provides methods
    to manipulate and/or read element values of the XML document.
    """

    doc_content = None
    ted = None

    uuid = None
    path = None
    task_config = None

    def __init__(self, doc_content, ted):
        self.doc_content = doc_content
        self.ted = ted
        self.uuid = self.get_uuid()
        self.path = self.get_path()
        self.task_config = self.get_task_config()

    @classmethod
    def from_content(cls, doc_content):
        """
        Alternative constructor (initialise from content string)

        @type doc_content: str
        @param doc_content: doc_content

        @rtype: TaskExecutionXml
        @return: TaskExecutionXml object
        """
        doc_content = doc_content
        ted = Etree.fromstring(doc_content)
        return cls(doc_content, ted)

    @classmethod
    def from_path(cls, xml_file_path):
        """
        Alternative constructor (initialise from xml file)

        @type xml_file_path: str
        @param xml_file_path: xml_file_path

        @rtype: TaskExecutionXml
        @return: TaskExecutionXml object
        """
        with open(xml_file_path, 'r') as xml_file:
            doc_content = xml_file.read()
        ted = Etree.fromstring(doc_content)
        xml_file.close()
        return cls(doc_content, ted)

    @classmethod
    def from_parameters(cls, uuid, path, task_config):
        """
        Alternative constructor (initialise from parameters)

        @type uuid: str
        @param uuid: xml_file_path

        @type path: str
        @param path: xml_file_path

        @type task_config: TaskConfig
        @param task_config: TaskConfig object

        @rtype: TaskExecutionXml
        @return: TaskExecutionXml object
        """
        doc_content = prettify(cls.create_task_execution_doc(uuid, path, task_config))
        ted = Etree.fromstring(doc_content)
        return cls(doc_content, ted)

    @classmethod
    def create_task_execution_doc(cls, uuid, ip_path, task_config):
        """
        Alternative constructor (initialise from parameters)

        @type uuid: str
        @param uuid: xml_file_path

        @type ip_path: str
        @param ip_path: xml_file_path

        @type task_config: TaskConfig
        @param task_config: TaskConfig object

        @rtype: xml.etree.ElementTree.Element
        @return: task execution document
        """
        task_execution = Element('task_execution')
        state = SubElement(task_execution, 'state')
        parameters = SubElement(task_execution, 'parameters')
        uuid_elm = SubElement(parameters, 'uuid')
        uuid_elm.text = uuid
        ip_path_elm = SubElement(parameters, 'path')
        packagename = SubElement(parameters, 'packagename')
        identifier = SubElement(parameters, 'identifier')
        reception = SubElement(parameters, 'reception')
        ip_path_elm.text = ip_path_elm
        task_config_elm = SubElement(parameters, 'config')
        expected_status = SubElement(task_config_elm, "expected_status")
        expected_status.text = str(task_config.expected_status)
        success_status = SubElement(task_config_elm, "success_status")
        success_status.text = str(task_config.success_status)
        error_status = SubElement(task_config_elm, "error_status")
        error_status.text = str(task_config.error_status)
        ip_path_elm.text = ip_path
        return task_execution

    def get_task_config(self):
        """
        Get task configuration object

        @rtype: TaskConfig
        @return: TaskConfig object
        """
        return TaskConfig(self.ted.find('.//parameters/config/expected_status').text,
                          int(self.ted.find(".//parameters/config/success_status").text),
                          int(self.ted.find(".//parameters/config/error_status").text))

    def get_path(self):
        """
        Get path from task execution document

        @rtype: str
        @return: Path
        """
        return self.ted.find('.//parameters/path').text

    def get_packagename(self):
        """
        Get packagename

        @rtype: str
        @return: packagename
        """
        return self.ted.find('.//parameters/packagename').text

    def set_packagename(self, packagename):
        """
        Set packagename

        @type packagename: str
        @param packagename: packagename
        """
        self.ted.find('.//parameters/packagename').text = packagename

    def get_identifier(self):
        """
        Get identifier

        @rtype: str
        @return: identifier
        """
        return self.ted.find('.//parameters/identifier').text

    def set_identifier(self, identifier):
        """
        Set identifier

        @type outcome: str
        @param outcome: identifier
        """
        self.ted.find('.//parameters/identifier').text = identifier

    def set_reception(self, reception):
        """
        Set reception

        @type reception: str
        @param reception: reception
        """
        self.ted.find('.//parameters/reception').text = reception

    def get_reception(self):
        """
        Get reception

        @rtype: str
        @return: reception
        """
        return self.ted.find('.//parameters/reception').text

    def get_uuid(self):
        """
        Get uuid (identifier) task execution document

        @rtype: str
        @return: uuid (identifier)
        """
        return self.ted.find('.//parameters/uuid').text

    def set_state(self, state):
        """
        Set success result element value

        @type outcome: Boolean
        @param outcome: Result success (True/False)
        """
        self.ted.find('.//state').text = str(state)

    def get_state(self):
        """
        Get success value of result element.

        @rtype: Boolean
        @return: Result success (True/False)
        """
        return int(self.ted.find('.//state').text)

    def get_updated_doc_content(self):
        """
        Get updated document content (from task execution document)

        @rtype: Boolean
        @return: Result success (True/False)
        """
        return Etree.tostring(self.ted, encoding='UTF-8')

    def write_doc(self, xml_file_path):
        """
        Write document to file

        @type xml_file_path: str
        @param xml_file_path: XML file path
        """
        xml_content = Etree.tostring(self.ted, encoding='UTF-8')
        with open(xml_file_path, 'w') as output_file:
            output_file.write(xml_content)
        output_file.close()


if __name__ == "__main__":

    # from parameters
    print "from parameters"
    ted_fp = TaskExecutionXml.from_parameters("0b764a8c-b36d-41cf-9ebc-06441c9b94a2", "/var/data/earkweb/work/0b764a8c-b36d-41cf-9ebc-06441c9b94a2", TaskConfig("100", 200, 290))
    print ted_fp.path
    print ted_fp.uuid
    print ted_fp.task_config.expected_status
    print ted_fp.task_config.success_status
    print ted_fp.task_config.error_status
    print ted_fp.doc_content
    print "\n"

    # from example document
    print "from example document"
    example_doc_content = """<?xml version="1.0" ?>
<task_execution>
  <state>700</state>
  <parameters>
    <uuid>9b764a8c-b36d-41cf-9ebc-06441c9b94a9</uuid>
    <path>/var/data/earkweb/work/9b764a8c-b36d-41cf-9ebc-06441c9b94a9</path>
    <config>
      <expected_status>700</expected_status>
      <success_status>800</success_status>
      <error_status>890</error_status>
    </config>
  </parameters>
</task_execution>"""
    ted_fc = TaskExecutionXml.from_content(example_doc_content)
    print ted_fc.path
    print ted_fc.uuid
    print ted_fc.task_config.expected_status
    print ted_fc.task_config.success_status
    print ted_fc.task_config.error_status
    print ted_fc.doc_content
    ted_fc.write_doc("/tmp/test.xml")
    print "\n"

    # from file path
    print "from file path"
    ted_fc = TaskExecutionXml.from_path("/tmp/test.xml")
    print ted_fc.path
    print ted_fc.uuid
    print ted_fc.task_config.expected_status
    print ted_fc.task_config.success_status
    print ted_fc.task_config.error_status
    print ted_fc.doc_content