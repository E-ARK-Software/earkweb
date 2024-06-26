from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree as Etree

from eatb.utils.datetime import current_timestamp
from eatb.utils.xmlutils import prettify

from taskbackend.taskconfig import TaskConfig


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
    def from_parameters(cls, state=-1, locked_val=False, last_task_value='None'):
        doc_content = prettify(cls.create_task_execution_doc(state, locked_val, last_task_value))
        ted = Etree.fromstring(doc_content)
        return cls(doc_content, ted)

    @classmethod
    def create_task_execution_doc(cls, state_val=-1, locked_val=False, last_task_value='None'):
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
        last_task_elm = SubElement(ip_state, 'last_task')
        last_task_elm.text = last_task_value
        return ip_state

    def get_last_task(self):
        """
        Get last task

        @rtype: str
        @return: last task
        """
        last_task_elm = self.ted.find('.//last_task')
        last_task_value = 'None' if last_task_elm is None else last_task_elm.text
        return last_task_value

    def set_last_task(self, last_task_value):
        """
        Set document path

        @type last_task: str
        @param last_task: last task
        """
        last_task_elm = self.ted.find('.//last_task')
        if last_task_elm is None:
            last_task_elm = SubElement(self.ted, 'last_task')
        last_task_elm.text = last_task_value

    def get_identifier(self):
        """
        Get identifier

        @rtype: str
        @return: identifier
        """
        identifier_elm = self.ted.find('.//identifier')
        identifier_value = 'None' if identifier_elm is None else identifier_elm.text
        return identifier_value

    def set_identifier(self, identifier_value):
        """
        Set identifier

        @type identifier: str
        @param identifier: last task
        """
        identifier_elm = self.ted.find('.//identifier')
        if identifier_elm is None:
            identifier_elm = SubElement(self.ted, 'identifier')
        identifier_elm.text = identifier_value

    def get_version(self):
        """
        Get identifier

        @rtype: str
        @return: identifier
        """
        version_elm = self.ted.find('.//version')
        version_value = '00000' if version_elm is None else version_elm.text
        return version_value

    def set_version(self, version_value):
        """
        Set identifier

        @type identifier: str
        @param identifier: last task
        """
        version_elm = self.ted.find('.//version')
        if version_elm is None:
            version_elm = SubElement(self.ted, 'version')
        version_elm.text = version_value

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

    def set_state(self, state_value):
        """
        Set state value

        @type state: int
        @param state: Result success (True/False)
        """
        state_elm = self.ted.find('.//state')
        if state_elm is None:
            state_elm = SubElement(self.ted, 'state')
        state_elm.text = str(state_value)

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
        if locked_elm is None:
            locked_elm = SubElement(self.ted, 'locked')
        locked_elm.text = str(locked_value)

    def get_lastchange(self):
        """
        Get lastchange value.

        @rtype: str
        @return: lastchange value (timestamp)
        """
        lastchange_elm = self.ted.find('.//lastchange')
        if lastchange_elm is None:
            return ""
        else:
            return self.ted.find('.//lastchange').text

    def set_lastchange(self, lastchange_value):
        """
        Set lastchange value

        @type lastchange: str
        @param lastchange: lastchange (timestamp)
        """
        lastchange_elm = self.ted.find('.//lastchange')
        if lastchange_elm is None:
            lastchange_elm = SubElement(self.ted, 'lastchange')
        lastchange_elm.text = str(lastchange_value)

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
        # update timestamp
        self.set_lastchange(current_timestamp())
        xml_content = Etree.tostring(self.ted, encoding='UTF-8')

        xmlstr = minidom.parseString(Etree.tostring(self.ted)).toprettyxml(indent="\t", newl="\n", encoding="UTF-8")

        with open(xml_file_path, 'w') as output_file:
            output_file.write(xmlstr.decode("utf-8"))
        output_file.close()


if __name__ == "__main__":

    # from parameters
    print("from parameters")
    ted_fp = IpState.from_parameters(200, True)
    print(ted_fp.get_state())
    print("\n")

    # from example document
    print("from example document")
    example_doc_content = """<?xml version="1.0" ?>
<ip_state>
  <state>700</state>
</ip_state>"""
    ted_fc = IpState.from_content(example_doc_content)
    print(ted_fc.get_state())
    ted_fc.write_doc("/tmp/test.xml")
    print("\n")

    # from file path
    print("from file path")
    ted_fc = IpState.from_path("/tmp/test.xml")
    print(ted_fc.get_state())
    ip_state = IpState.from_parameters(50, True)
    print(ip_state.get_updated_doc_content())
    print("state: %d" % ip_state.get_state())
    print("\n")
    ip_state.set_state(100)
    print(ip_state.get_updated_doc_content())

    ip_state.set_locked(True)
    print(ip_state.get_updated_doc_content())
