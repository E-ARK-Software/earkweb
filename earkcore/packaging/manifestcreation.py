# coding=UTF-8
'''
Created on June 15, 2015
'''
from subprocess import check_output
import shutil
import os
from earkcore.process.cli.CliCommand import CliCommand
from earkcore.utils import randomutils
import unittest
import re
from config.config import root_dir

class ManifestCreation(object):
    """
    Create package file manifest using 'summain'
    """
    def __init__(self, working_directory):
        self.working_directory = working_directory
        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

    def create_manifest(self, package_dir, manifest_file):
        cli = CliCommand.get("summain", dict(manifest_file=manifest_file, package_dir=package_dir))
        print cli
        out = check_output(cli)
        return out


class TestManifestCreation(unittest.TestCase):
    aip_compound_dir = root_dir + '/earkresources/AIP-test/AIP-compound'
    temp_working_dir = root_dir + '/tmp/temp-aip-dir-' + randomutils.randomword(10) + "/"
    manifest_file = os.path.join(temp_working_dir, './manifest.mf')

    manifest_creation = ManifestCreation(temp_working_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TestManifestCreation.temp_working_dir)

    def get_file_entry(self, s):
        file_pattern = re.compile(r"""Name: (?P<name>.*)\nMtime: (?P<time>.*)\nSize: (?P<size>.*)""", re.VERBOSE)
        file_match = file_pattern.match(s)
        if file_match is not None:
            return {'name': file_match.group("name").strip(), 'time': file_match.group("time").strip(), 'size': file_match.group("size").strip()}
        else:
            return None

    def test_create_manifest(self):
        self.manifest_creation.create_manifest(self.aip_compound_dir, self.manifest_file)
        self.assertTrue(os.path.isfile(self.manifest_file), ("File %s not found in working directory" % file))
        print self.manifest_file
        entries = open(self.manifest_file).read().split("\n\n")
        for entry in entries:
            file_entry = self.get_file_entry(entry)
            if file_entry is not None:
                actual_size = int(os.path.getsize(file_entry['name']))
                entry_size = int(file_entry['size'])
                self.assertTrue(os.path.isfile(file_entry['name']), "File must exist")
                self.assertEquals(actual_size, entry_size, "File size must match")


if __name__ == '__main__':
    unittest.main()
