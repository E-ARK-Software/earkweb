import os
from earkcore.filesystem.fsinfo import fsize


def default_reporter(percent):
    print "\r{percent:3.0f}%".format(percent=percent)


class FileBinaryDataChunks(object):
    """
    Generator to iteratively read binary chunks of a large file
    """

    def __init__(self, filepath, chunksize=65536, progress_reporter=default_reporter):
        """
        Initialise object with file path and chunksize
        :param filepath: File path
        :param chunksize: Chunk size
        """
        self.filepath = filepath
        self.chunksize = chunksize
        self.progress_reporter = progress_reporter
        self.current_file_size = os.path.getsize(filepath)
        self.bytesread = 0

    def chunks(self, total_bytes_read=0, bytes_total=-1):
        """
        Chunk generator, returns data chunks which can be iterated in a for loop.
        :return: generator with data chunks
        """
        if bytes_total == -1:
            bytes_total = self.current_file_size
        f = open(self.filepath, 'rb')

        def readchunk():
            return f.read(self.chunksize)

        for chunk in iter(readchunk, ''):
            self.bytesread += len(chunk)
            percent = (total_bytes_read+self.bytesread) * 100 / bytes_total
            self.progress_reporter(percent)
            yield chunk

def copy_file(source, target, progress_reporter=default_reporter, total_bytes_read=0, bytes_total=-1):
    with open(target, 'wb') as target_file:
        for chunk in FileBinaryDataChunks(source, 65536, progress_reporter).chunks(total_bytes_read, total_bytes_read):
            target_file.write(chunk)
        target_file.close()
        total_bytes_read += fsize(source)
    return total_bytes_read
