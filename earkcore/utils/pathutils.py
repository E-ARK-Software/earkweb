import os
import unittest
import pytz
import datetime


def strip_prefixes(path, *prefixes):
    prefix_part = os.path.join(os.path.join(*prefixes), '')
    return path.replace(prefix_part, '')


def backup_file_path(abs_path):
    path, filename = os.path.split(abs_path)
    basename, extension = os.path.splitext(filename)
    dt = datetime.datetime.now(tz=pytz.timezone('Europe/Vienna'))
    ts = dt.strftime("%Y%m%d%H%M%S")
    backup_file_name = "%s_%s%s" % (basename, ts, extension)
    return os.path.join(path, backup_file_name)


class TestPathFunctions(unittest.TestCase):

    def test_strip_prefixes_from_path_singlefile(self):
        full_path = '/to/be/stripped/someotherpart/file.txt'
        path_part1 = '/to/be/stripped'
        path_part2 = 'someotherpart'
        self.assertEqual('file.txt', strip_prefixes(full_path, path_part1, path_part2))

    def test_strip_prefixes_from_path_file_in_subdir(self):
        full_path = '/to/be/stripped/someotherpart/sub/dir/file.txt'
        path_part1 = '/to/be/stripped'
        path_part2 = 'someotherpart'
        self.assertEqual('sub/dir/file.txt', strip_prefixes(full_path, path_part1, path_part2))

    def test_strip_single_prefix_from_path(self):
        full_path = '/to/be/stripped/someotherpart/file.txt'
        path_part = '/to/be/stripped'
        self.assertEqual('someotherpart/file.txt', strip_prefixes(full_path, path_part))


if __name__ == '__main__':
    unittest.main()
