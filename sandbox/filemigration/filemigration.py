import os, sys
import time, os

# initialise django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()
import unittest

##########################
##########################

from earkcore.format.formatidentification import FormatIdentification
from earkcore.process.cli.CliCommand import CliCommand
import subprocess32
from subprocess import call

pdf = ['fmt/14', 'fmt/15', 'fmt/16', 'fmt/17', 'fmt/18', 'fmt/19', 'fmt/20', 'fmt/276']

class FileMigration():
    # check migration rules
    # migrate the file
    # add premis event

    def __init__(self, source_path, target_path):
        self.identification = FormatIdentification()

        if not os.path.exists(target_path):
            os.makedirs(target_path)

        self.target_path = target_path
        self.source_path = source_path

        for directory, subdirectory, filenames in os.walk(source_path):
            for filename in filenames:
                fido_result = self.identification.identify_file(os.path.join(source_path, filename))
                if fido_result in pdf:
                    migration = self.migrate(filename, fido_result)


    def migrate(self, file, fido_result):
        # TODO: migration depending of fido_result
        print 'File %s identified as %s' % (file, fido_result)

        # TODO: avoid having '-sOutputFile=' here
        cliparams = {'output_file': '-sOutputFile=' + os.path.join(self.target_path, file),
                     'input_file': os.path.join(self.source_path, file)}
        args = CliCommand.get('pdftopdfa', cliparams)
        migrate = subprocess32.Popen(args)
        # note: the following line has to be there, even if nothing is done with out/err messages,
        # as the process will otherwise deadlock!
        out, err = migrate.communicate()

        return True if err == None else False



class TestMigration(unittest.TestCase):
    path = '/var/data/earkweb/work/7449629c-9e67-44d6-a10e-21d1fdfa4ebd/submission/representations/rep-001/data'
    target = '/var/data/earkweb/work/7449629c-9e67-44d6-a10e-21d1fdfa4ebd/submission/representations/rep-002/data'

    def test_migration(self):
        # scan AIP for representations
        # take newest (highest rep-number)
        # create new rep, create premis file
        # identify files in there that can be migrated (fido) -> premis?
        # migrate -> premis event

        FileMigration(self.path, self.target)


if __name__ == '__main__':
    unittest.main()