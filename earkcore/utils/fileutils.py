from shutil import copytree
import os

def copytree(self, origin_dir, target_dir):
    """
    Copy extracted SIP to working area

    @type       extracted_sip_directory: string
    @param      extracted_sip_directory: Path to extracted SIP directory
    @rtype:     bool
    @return:    Success of AIP preparation
    """
    copytree(origin_dir, target_dir)