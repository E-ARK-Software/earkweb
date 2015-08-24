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

def main():
    print remove_protocol("file://./test")

if __name__ == "__main__":
    main()