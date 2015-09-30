from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree as Etree
from earkcore.utils.xmlutils import prettify
from workers.taskconfig import TaskConfig


class IpState(object):
    """
    TaskExecutionXml class which represents an XML document to persist task execution parameters and results.
    The class can be initiated by parameters (static method from_parameters), by XML content string (static
    method from_content), or by an XML file path (static method from_path). Furthermore, it provides methods
    to manipulate and/or read element values of the XML document.
    """

    doc_content = None
    ted = None

    doc_path = None

    def __init__(self, doc_content, ted):
        self.doc_content = doc_content
        self.ted = ted

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
    def from_parameters(cls, state, locked_val):
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
        doc_content = prettify(cls.create_task_execution_doc(state, locked_val))
        ted = Etree.fromstring(doc_content)
        return cls(doc_content, ted)

    @classmethod
    def create_task_execution_doc(cls, state_val, locked_val):
        """
        Alternative constructor (initialise from parameters)

        @type state_val: int
        @param state_val: state value

        @rtype: xml.etree.ElementTree.Element
        @return: task execution document
        """
        ip_state = Element('ip_state')
        state_elm = SubElement(ip_state, 'state')
        state_elm.text = str(state_val)
        locked_elm = SubElement(ip_state, 'locked')
        locked_elm.text = str(locked_val)
        return ip_state

    def get_doc_path(self):
        """
        Get document path

        @rtype: str
        @return: document path
        """
        return self.doc_path

    def set_doc_path(self, doc_path):
        """
        Set document path

        @type doc_path: str
        @param doc_path: document path
        """
        self.doc_path = doc_path

    def get_state(self):
        """
        Get state value.

        @rtype: int
        @return: state value
        """
        return int(self.ted.find('.//state').text)

    def set_state(self, state):
        """
        Set state value

        @type state: int
        @param state: Result success (True/False)
        """
        state_elm = self.ted.find('.//state')
        state_elm.text = str(state)

    def get_locked(self):
        """
        Get locked value.

        @rtype: bool
        @return: locked value
        """
        return self.ted.find('.//locked').text == "True"

    def set_locked(self, locked_value):
        """
        Set locked value

        @type locked: bool
        @param locked: locked (True/False)
        """
        locked_elm = self.ted.find('.//locked')
        if not locked_elm:
            locked_elm = SubElement(self.ted, 'locked')
        locked_elm.text = str(locked_value)

    def get_updated_doc_content(self):
        """
        Get updated document content (from task execution document)

        @rtype: str
        @return: Updated XML document content
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
    ted_fp = IpState.from_parameters(200, True)
    print ted_fp.get_state()
    print "\n"

    # from example document
    print "from example document"
    example_doc_content = """<?xml version="1.0" ?>
<ip_state>
  <state>700</state>
</ip_state>"""
    ted_fc = IpState.from_content(example_doc_content)
    print ted_fc.get_state()
    ted_fc.write_doc("/tmp/test.xml")
    print "\n"

    # from file path
    print "from file path"
    ted_fc = IpState.from_path("/tmp/test.xml")
    print ted_fc.get_state()
    ip_state = IpState.from_parameters(50, True)
    print ip_state.get_updated_doc_content()
    print "state: %d" % ip_state.get_state()
    print "\n"
    ip_state.set_state(100)
    print ip_state.get_updated_doc_content()

    ip_state.set_locked(True)
    print ip_state.get_updated_doc_content()
