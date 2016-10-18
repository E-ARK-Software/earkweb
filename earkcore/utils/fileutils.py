from shutil import copytree
from shutil import rmtree
import os
import errno
import fnmatch
import shutil
import unittest

MAX_TRIES = 10000

# def copytree(self, origin_dir, target_dir):
#     """
#     Copy extracted SIP to working area
#
#     @type       extracted_sip_directory: string
#     @param      extracted_sip_directory: Path to extracted SIP directory
#     @rtype:     bool
#     @return:    Success of AIP preparation
#     """
#     copytree(origin_dir, target_dir)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def remove_dir(path):
    if os.path.isdir(path):
        rmtree(path)


def remove_fs_item(uuid, working_dir, rel_path):
    abs_path = os.path.join(working_dir, rel_path)
    if working_dir.endswith(uuid) and os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            rmtree(abs_path)
        else:
            os.remove(abs_path)


def remove_protocol(path_with_protocol):
    # expand this array if necessary (more complex ones come first, subsets of complex ones after them)
    protocols = ['file://', 'file:', 'file/']
    for prot in protocols:
        stripped_path = path_with_protocol.replace(prot, '')
        if len(stripped_path) < len(path_with_protocol):
            return stripped_path
    return path_with_protocol


def copy_tree_content(source_dir, target_dir):
    fs_childs = os.listdir(source_dir)
    for fs_child in fs_childs:
        source_item = os.path.join(source_dir, fs_child)
        copytree(source_item, os.path.join(target_dir, fs_child))


def move_folder_content(source_dir, target_dir):
    fs_childs = os.listdir(source_dir)
    for fs_child in fs_childs:
        source_item = os.path.join(source_dir, fs_child)
        shutil.move(source_item, target_dir)


def force_merge_flat_dir(srcDir, dstDir):
    if not os.path.exists(dstDir):
        os.makedirs(dstDir)
    for item in os.listdir(srcDir):
        srcFile = os.path.join(srcDir, item)
        dstFile = os.path.join(dstDir, item)
        secure_force_copy_file(srcFile, dstFile)


def secure_force_copy_file(sfile, dfile):
    if os.path.isfile(sfile):
        shutil.copy2(sfile, dfile)
        from earkcore.fixity.ChecksumFile import get_sha256_hash
        if not os.path.exists(dfile) or not get_sha256_hash(sfile) == get_sha256_hash(dfile):
            raise IOError("File copy operation failed  (checksums are not equal comparing %s and %s)." % (sfile, dfile))


def is_flat_dir(sDir):
    for item in os.listdir(sDir):
        sItem = os.path.join(sDir, item)
        if os.path.isdir(sItem):
            return False
    return True


def secure_copy_tree(src, dst):
    try:
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isfile(s):
                if not os.path.exists(dst):
                    os.makedirs(dst)
                secure_force_copy_file(s,d)
            if os.path.isdir(s):
                is_recursive = not is_flat_dir(s)
                if is_recursive:
                    secure_copy_tree(s, d)
                else:
                    force_merge_flat_dir(s, d)
        return True
    except IOError, err:
        print err
        return False

def delete_directory_content(root_dir):
    fs_childs = os.listdir(root_dir)
    for fs_child in fs_childs:
        item = os.path.join(root_dir, fs_child)
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

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
    while i < MAX_TRIES:
        suffix = '%05d' % i
        inc_file_name = "%s_%s.%s" % (abspath_basename, suffix, extension)
        if not os.path.exists(inc_file_name):
                return inc_file_name
        i += 1


def latest_aip(abspath_basename, extension):
    """
    Get file with highest suffix
    @type       abspath_basename: string
    @param      abspath_basename: absolute path without extension
    @type       extension: string
    @param      extension: file extension
    @rtype:     string
    @return:    incremented file path
    """
    i = 1
    file_candidate = None
    while i < MAX_TRIES:
        suffix = '%05d' % i
        inc_file_name = "%s_%s.%s" % (abspath_basename, suffix, extension)
        if not os.path.exists(inc_file_name):
                return file_candidate
        file_candidate = inc_file_name
        i += 1


def read_file_content(file_path):
    fh = open(file_path, 'r')
    file_content = fh.read()
    return file_content


def locate(pattern, root_path):
    for path, dirs, files in os.walk(os.path.abspath(root_path)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


class TestPathFunctions(unittest.TestCase):

    def test_remove_protocol(self):
        self.assertEqual('./test', remove_protocol("file://./test"))


def copy_folder(src, dest):
    _, leaf_folder = os.path.split(src)
    shutil.copytree(src, os.path.join(dest, leaf_folder))
    if os.path.exists(dest):
        print "Folder \"%s\" moved to target directory: \"%s\"" % (src, dest)
    else:
        print "Failed moving folder \"%s\" to \"%s\"" % (src, dest)


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def sub_dirs(a_dir):
    return sorted([name for name in os.listdir(a_dir) if os.path.isdir(os.path.join(a_dir, name))])


if __name__ == '__main__':
    unittest.main()
