# coding=UTF-8
"""
Created on June 9, 2015
Modified on May 9 2016 (puid to mime)

@author: Jan Rörden
@author: Sven Schlarb
"""

import unittest
from fido.fido import Fido


class FormatIdentification():
    """
    File Format Identification
    """

    def __init__(self):
        self.fid = Fido()
        self.fid.handle_matches = self.print_matches
        self.lastFmt = None

    def identify_file(self, entry):
        """
        This function identifies the file format of every file that is handed over.
        """
        self.fid.identify_file(entry)
        return self.lastFmt

    def get_mime_for_puid(self, puid):
        """
        Get mime type for a given puid

        @type       puid: string
        @param      puid: PRONOM Persistent Unique Identifier

        @rtype:     string
        @return:    mime type string (default: application/octet-stream)
        """
        mime_tag = "mime"
        fmtres = self.fid.puid_format_map[puid]
        childs = [child for child in fmtres if child.tag.endswith(mime_tag)]
        if len(childs) == 1:
            return (childs[0]).text.strip()
        else:
            return "application/octet-stream"

    def print_matches(self, fullname, matches, delta_t, matchtype=''):
        # print "####" + fullname
        for (f, s) in matches:
            self.lastFmt = self.fid.get_puid(f)


class TestFormatIdentification(unittest.TestCase):
    def testFido(self):
        ffid = FormatIdentification()
        puid = ffid.identify_file("../../earkresources/schemas/xlink.xsd")
        self.assertTrue("x-fmt/280", puid)
        self.assertEqual("application/xml", ffid.get_mime_for_puid(puid))

if __name__ == '__main__':
    unittest.main()
