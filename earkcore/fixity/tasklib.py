from earkcore.filesystem.chunked import FileBinaryDataChunks
from earkcore.filesystem.fsinfo import fsize
from earkcore.fixity.ChecksumFile import ChecksumFile
from earkcore.fixity.ChecksumAlgorithm import ChecksumAlgorithm

def check_transfer(source, target, tl):
    source_size = fsize(source)
    target_size = fsize(target)
    if not source_size == target_size:
        tl.adderr("Size of source file (%d bytes) and size of target file (%d bytes) are not equal" % (source_size, target_size))
    if not ChecksumFile(source).get(ChecksumAlgorithm.SHA256) == ChecksumFile(target).get(ChecksumAlgorithm.SHA256):
        tl.adderr("Checksums of source %s and target %s are not equal" % (source, target))