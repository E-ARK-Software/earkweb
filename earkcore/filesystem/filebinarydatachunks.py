import os


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
        self.totalsize = os.path.getsize(filepath)
        self.bytesread = 0

    def chunks(self):
        """
        Chunk generator, returns data chunks which can be iterated in a for loop.
        :return: generator with data chunks
        """
        f = open(self.filepath, 'rb')

        def readchunk():
            return f.read(self.chunksize)

        for chunk in iter(readchunk, ''):
            self.bytesread += len(chunk)
            percent = self.bytesread * 100 / self.totalsize
            self.progress_reporter(percent)
            yield chunk
