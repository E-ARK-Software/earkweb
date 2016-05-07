# coding=UTF-8
"""
Created on April 30, 2016

@author: Sven Schlarb (https://github.com/shsdev)
"""
import logging
logger = logging.getLogger(__name__)

import shutil

from earkcore.fixity.ChecksumFile import ChecksumFile
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm

import os
import os.path
import unittest
import ntpath
import tarfile
from earkcore.utils import randomutils

from config.configuration import root_dir

from pairtree import PairtreeStorageFactory, ObjectNotFoundException

VersionDirFormat = '%05d'


def default_reporter(percent):
    print "\rProgress: {percent:3.0f}%".format(percent=percent)


class PairtreeStorage(object):
    """
    Pairtree storage class allowing to build a filesystem hierarchy for holding objects that are located by mapping identifier strings to object directory (or folder) paths with
    two characters at a time.
    """

    storage_factory = None
    repository_storage_dir = None

    """
    Constructor initialises pairtree repository

    @type       repository_storage_dir: string
    @param      repository_storage_dir: repository storage directory
    """
    def __init__(self, repository_storage_dir):
        self.storage_factory = PairtreeStorageFactory()
        self.repository_storage_dir = repository_storage_dir
        self.repo_storage_client = self.storage_factory.get_store(store_dir=self.repository_storage_dir, uri_base="http://")

    """
    Storing an object in the pairtree path according to the given identifier. If a version of the object exists,
    a new version is created.

    @type       identifier: string
    @param      identifier: Identifier
    @type:      source_file: string
    @param:     source_file: Source file path to be stored in the repository
    @type:      progress_reporter: function
    @param:     progress_reporter: progress reporter function
    @raise:     IOError: If the checksum of the copied file is incorrect
    """
    def store(self, identifier, source_file, progress_reporter=default_reporter):
        repo_object = self.repo_storage_client.get_object(identifier, True)
        basename = ntpath.basename(source_file)
        next_version = self._next_version(identifier)
        with open(source_file, 'rb') as stream:
            repo_object.add_bytestream(basename, stream, path="data/%s" % next_version)
        progress_reporter(50)
        checksum_source_file = ChecksumFile(source_file).get(ChecksumAlgorithm.SHA256)
        checksum_target_file = ChecksumFile(self.get_object_path(identifier)).get(ChecksumAlgorithm.SHA256)
        if checksum_source_file != checksum_target_file:
            raise IOError("Storage of repository object for identifier '%s' failed!" % identifier)
        progress_reporter(100)

    """
    Verify if an object of the given identifier exists in the repository

    @type       identifier: string
    @param      identifier: Identifier
    @rtype:     boolean
    @return:    True if the object exists, false otherwise
    """
    def identifier_object_exists(self, identifier):
        logger.debug("Looking for object at path: %s/data" % self.repo_storage_client._id_to_dirpath(identifier))
        return self.repo_storage_client.exists(identifier, "data")

    """
    Verify if the given version of the object exists in the repository

    @type       identifier: string
    @param      identifier: Identifier
    type        version_num: int
    @param      version_num: version number
    @rtype:     boolean
    @return:    True if the object exists, false otherwise
    """
    def identifier_version_object_exists(self, identifier, version_num):
        version = '%05d' % version_num
        return self.repo_storage_client.exists(identifier, "data/%s" % version)

    """
    Get version directories

    @type       identifier: string
    @param      identifier: Identifier
    @rtype:     list
    @return:    List of directories of the versions
    """
    def _get_version_parts(self, identifier):
        return self.repo_storage_client.list_parts(identifier, "data")

    """
    Get next formatted version directory name

    @type       identifier: string
    @param      identifier: Identifier
    @rtype:     string
    @return:    Formatted version string (constant VersionDirFormat)
    """
    def _next_version(self, identifier):
        if not self.identifier_object_exists(identifier):
            return VersionDirFormat % 1
        version_num = 1
        while self.identifier_version_object_exists(identifier, version_num):
            version_num += 1
        return VersionDirFormat % version_num

    """
    Get current formatted version directory name

    @type       identifier: string
    @param      identifier: Identifier
    @rtype:     string
    @return:    Formatted version string (constant VersionDirFormat)
    """
    def curr_version(self, identifier):
        return VersionDirFormat % self.curr_version_num(identifier)

    """
    Get current version number

    @type       identifier: string
    @param      identifier: Identifier
    @rtype:     int
    @return:    Current version number
    """
    def curr_version_num(self, identifier):
        if not self.identifier_object_exists(identifier):
            raise ValueError("No repository object for id '%s'. Unable to get current version number." % identifier)
        version_num = 1
        while self.identifier_version_object_exists(identifier, version_num):
            version_num += 1
        version_num -= 1
        return version_num

    """
    Get absolute file path of the stored object. If the version number is omitted, the path of the highest version
    number is returned.

    @type       identifier: string
    @param      identifier: Identifier
    @type       version_num: int
    @param      version_num: version number
    @rtype:     string
    @return:    Absolute file path of the stored object
    @raise      ObjectNotFoundException if the file is not available
    """
    def get_object_path(self, identifier, version_num=0):
        if not self.identifier_object_exists(identifier):
            raise ValueError("No repository object for id '%s'. Unable to get requested version object path." % identifier)
        if version_num == 0:
            version_num = self.curr_version_num(identifier)
        if not self.identifier_version_object_exists(identifier, version_num):
            raise ValueError("Repository object '%s' has no version %d." % (identifier, version_num))
        version = '%05d' % version_num
        repo_obj = self.repo_storage_client.get_object(identifier, False)
        repo_obj_path = os.path.join(repo_obj.id_to_dirpath(), "data/%s" % version)
        try:
            return next(os.path.join(repo_obj_path, f) for f in os.listdir(repo_obj_path) if os.path.isfile(os.path.join(repo_obj_path, f)))
        except StopIteration:
            raise ObjectNotFoundException("The file object does not exist in the repository")

    """
    Get stream of tar file entry.

    @type       identifier: string
    @param      identifier: Identifier
    @type       entry: string
    @param      entry: tar file entry (path within tar file)
    @rtype:     binary
    @return:    File content
    @raise      KeyError if the tar entry does not exist in the stored package
    """
    def get_object_item_stream(self, identifier, entry):
        object_path = self.get_object_path(identifier)
        t = tarfile.open(object_path, 'r')
        logger.debug("Trying to access entry %s" % entry)
        try:
            info = t.getmember(entry)
            f=t.extractfile(info)
            return f.read()
        except KeyError:
            logging.error('ERROR: Did not find %s in tar archive' % entry)
            raise ObjectNotFoundException("Entry not found in repository object")

class TestPairtreeStorage(unittest.TestCase):
    source_dir = root_dir + '/earkresources/storage-test/'
    package_file = "bar.tar"
    repository_storage_dir = root_dir + '/tmp/temp-' + randomutils.randomword(10)
    test_repo = root_dir + '/earkresources/test-repo/'

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TestPairtreeStorage.repository_storage_dir):
            os.makedirs(TestPairtreeStorage.repository_storage_dir)
        shutil.copy(os.path.join(TestPairtreeStorage.test_repo, "pairtree_version0_1"), TestPairtreeStorage.repository_storage_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TestPairtreeStorage.repository_storage_dir)

    def test_identifier_object_exists(self):
        pts = PairtreeStorage(TestPairtreeStorage.test_repo)
        existing_identifier = "bar"
        nonexisting_identifier = "foo"
        self.assertEquals(pts.identifier_object_exists(existing_identifier),True)
        self.assertEquals(pts.identifier_object_exists(nonexisting_identifier),False)

    def test_version_exists(self):
        pts = PairtreeStorage(TestPairtreeStorage.test_repo)
        identifier = "bar"
        self.assertEquals(pts.identifier_version_object_exists(identifier, 3),False)
        self.assertEquals(pts.identifier_version_object_exists(identifier, 2),True)

    def test_next_version(self):
        pts = PairtreeStorage(TestPairtreeStorage.test_repo)
        identifier = "bar"
        self.assertEquals("00003", pts._next_version(identifier))

    def test_curr_version(self):
        pts = PairtreeStorage(TestPairtreeStorage.test_repo)
        identifier = "bar"
        self.assertEquals("00002", pts.curr_version(identifier))

    def test_store(self):
        pts = PairtreeStorage(TestPairtreeStorage.repository_storage_dir)
        pts.store("bar", os.path.join(self.source_dir, self.package_file))
        self.assertEqual(1, pts.curr_version_num("bar"))
        pts.store("bar", os.path.join(self.source_dir, self.package_file))
        self.assertEqual(2, pts.curr_version_num("bar"))

    def test_get_object_path(self):
        pts = PairtreeStorage(TestPairtreeStorage.test_repo)
        expected = os.path.join(TestPairtreeStorage.test_repo, "pairtree_root/ba/r/data/00002/bar.tar")
        actual = pts.get_object_path("bar")
        self.assertEqual(expected, actual)

    def test_get_object_item_stream(self):
        pts = PairtreeStorage(TestPairtreeStorage.test_repo)

        content = pts.get_object_item_stream("bar", "739f9c5f-c402-42af-a18b-3d0bdc4e8751/METS.xml")
        self.assertTrue(content.startswith("<?xml"))
        logger.debug(content)

if __name__ == '__main__':
    unittest.main()
