#!/usr/bin/env python
# coding=UTF-8
__author__ = "Jan Rörden, Roman Graf, Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

import unittest
import os
import tarfile

def default_reporter(percent):
    print "\r{percent:3.0f}%".format(percent=percent)

from config.configuration import root_dir

class ChunkedTarEntryReader(object):
    """
    Chunked TAR entry reader allowing to read large TAR entries.
    """

    def __init__(self, tfile, chunksize=512):
        self.tfile = tfile
        self.chunksize = chunksize
        self.bytesread = 0

    def chunks(self, entry, total_bytes_read=0, bytes_total=-1):
        """
        Chunk generator, returns data chunks which can be iterated in a for loop.
        :return: generator with data chunks
        """
        tinfo = self.tfile.getmember(entry)

        if bytes_total == -1:
            bytes_total = tinfo.size
        f = self.tfile.extractfile(tinfo)

        def readchunk():
            return f.read(self.chunksize)

        for chunk in iter(readchunk, ''):
            self.bytesread += len(chunk)
            percent = (total_bytes_read+self.bytesread) * 100 / bytes_total
            default_reporter(percent)
            yield chunk


class ChunkedTarEntryReaderTest(unittest.TestCase):

    tar_test_file = None
    entry = None
    tfile = None

    @classmethod
    def setUpClass(cls):
        ChunkedTarEntryReaderTest.tar_test_file = os.path.join(root_dir, "earkresources/storage-test/bar.tar")
        ChunkedTarEntryReaderTest.entry = "739f9c5f-c402-42af-a18b-3d0bdc4e8751/METS.xml"
        ChunkedTarEntryReaderTest.tfile = tarfile.open(ChunkedTarEntryReaderTest.tar_test_file, 'r')

    def test_default_chunk_size(self):
        cter1 = ChunkedTarEntryReader(ChunkedTarEntryReaderTest.tfile)
        self.assertEqual(12, sum([1 for c in cter1.chunks(ChunkedTarEntryReaderTest.entry)]))
        cter1 = ChunkedTarEntryReader(ChunkedTarEntryReaderTest.tfile)

    def test_custom_chunk_size(self):
        cter2 = ChunkedTarEntryReader(ChunkedTarEntryReaderTest.tfile, 8192)
        self.assertEqual(1, sum([1 for c in cter2.chunks(ChunkedTarEntryReaderTest.entry)]))
        cter2 = ChunkedTarEntryReader(ChunkedTarEntryReaderTest.tfile)

if __name__ == '__main__':
    unittest.main()