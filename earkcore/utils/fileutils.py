from shutil import copytree
import os, errno
from earkcore.utils.stringutils import lstrip_substring

def copytree(self, origin_dir, target_dir):
    """
    Copy extracted SIP to working area

    @type       extracted_sip_directory: string
    @param      extracted_sip_directory: Path to extracted SIP directory
    @rtype:     bool
    @return:    Success of AIP preparation
    """
    copytree(origin_dir, target_dir)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def remove_protocol(path_with_protocol):
    return lstrip_substring(path_with_protocol, 'file://')


def increment_file_name_suffix(abspath_basename, extension):
        """
        Increment file name suffix depending on existing files: append generation number to file; if tar file exists, the suffix number is incremented
        @type       abspath_basename: string
        @param      abspath_basename: absolute path without extension
        @type       extension: string
        @param      extension: file extension
        @rtype:     string
        @return:    incremented file path
        """
        i = 1
        while i > 0:
                suffix = '%05d' % i
                inc_file_name = "%s_%s.%s" % (abspath_basename, suffix, extension)
                if not os.path.exists(inc_file_name):
                        return inc_file_name
                        i = -1 # break condition
                i+=1


def main():
    print remove_protocol("file://./test")

if __name__ == "__main__":
    main()