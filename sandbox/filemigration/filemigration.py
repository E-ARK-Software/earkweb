import os, sys
import time, os

# initialise django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()
import unittest

from memory_profiler import profile

##########################
##########################

from earkcore.format.formatidentification import FormatIdentification
from earkcore.process.cli.CliCommand import CliCommand
import subprocess32
import multiprocessing
from multiprocessing import Process
import time

pdf = ['fmt/14', 'fmt/15', 'fmt/16', 'fmt/17', 'fmt/18', 'fmt/19', 'fmt/20', 'fmt/276']
gif = ['fmt/3', 'fmt/4']

class FileMigration():
    # check migration rules
    # migrate the file
    # add premis event
    # TODO: feedback to frontend about number of files being migrated (and that the programm is still running)

    def __init__(self, source_path, target_path):
        self.identification = FormatIdentification()

        if not os.path.exists(target_path):
            os.makedirs(target_path)

        self.target_path = target_path
        self.source_path = source_path

        self.total = 0
        self.success = 0
        self.failure = 0

        print multiprocessing.current_process().name
        self.start()

    def start(self):
        print 'Starting the migration process, this might take a while.'

        for directory, subdirectory, filenames in os.walk(self.source_path):
            for filename in filenames:
                fido_result = self.identification.identify_file(os.path.join(self.source_path, filename))
                # change: if fido_result indicates that a file should be migrated - i.e. create some kind of migration policy
                if fido_result in pdf:
                    # start a new process (multiprocessing to migrate multiple files at once)
                    migration = Process(target=self.pdf_to_pdfa, args=(filename,))
                    migration.start()
                    migration.join()
                    self.total += 1
                elif fido_result in gif:
                    # start a new process (multiprocessing to migrate multiple files at once)
                    migration = Process(target=self.gif_to_tiff, args=(filename,))
                    migration.start()
                    migration.join()
                    self.total += 1
                elif fido_result:
                    pass

        return True
        #self.feedback = Process(target=self.migrationwatch())
        #self.feedback.start()

    # @profile
    def pdf_to_pdfa(self, file):
        # TODO: additional sub-structure of rep/data when creating target path
        print 'File %s is now migrated to PDF/A.' % file

        # TODO: avoid having '-sOutputFile=' here
        cliparams = {'output_file': '-sOutputFile=' + os.path.join(self.target_path, file),
                     'input_file': os.path.join(self.source_path, file)}
        args = CliCommand.get('pdftopdfa', cliparams)

        # TODO: error handling (OSException)
        migrate = subprocess32.Popen(args)
        # note: the following line has to be there, even if nothing is done with out/err messages,
        # as the process will otherwise deadlock!
        out, err = migrate.communicate()
        if err == None:
            self.success += 1
        else:
            self.failure += 1
        self.total -= 1

    def gif_to_tiff(self, file):
        print 'File %s is now migrated to TIFF.' % file

        outputfile = file.rsplit('.', 1)[0] + '.tiff'
        cliparams = {'input_file': os.path.join(self.source_path, file),
                     'output_file': os.path.join(self.target_path, outputfile)}
        args = CliCommand.get('totiff', cliparams)

        migrate = subprocess32.Popen(args)
        # note: the following line has to be there, even if nothing is done with out/err messages,
        # as the process will otherwise deadlock!
        out, err = migrate.communicate()
        if err == None:
            self.success += 1
        else:
            self.failure += 1
        self.total -= 1


    #def migrationwatch(self):
    #    print 'Migrating a total of %d files. Updating every five seconds...' % self.total
    #    while (self.success + self.failure != self.total):
    #        print 'Migrated %d files, %d migrations have failed. %d migrations in progress.' % (self.success, self.failure, self.total)
    #        time.sleep(5)



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