from subprocess import check_output
import lxml

def get_jhove(file):
    out = check_output(["/usr/bin/jhove", "-h", "XML", "-i", file])
    parsed = lxml.etree.fromstring(out)
    result = lxml.etree.tostring(parsed, xml_declaration=False)
    return result