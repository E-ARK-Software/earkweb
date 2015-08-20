#!/usr/bin/env python
# coding=UTF-8
__author__ = "Jan Rörden, Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

import unittest
import string
from config.commands import commands


class CliCommand(object):
    """
    CliCommand class
    Get a Command Line Interface (CLI) command based on templates defined in the configuration (config.commands).
    """

    # commands are defined in the configuration
    _commands = commands

    @staticmethod
    def get(name, subst):
        """
        Get a Command Line Interface (CLI) command based on templates defined in the configuration (config.commands).

        @type       name: string
        @param      name: CLI command name
        @type       subst:  dict
        @param      subst:  Dictionary of substitution variables (e.g. {'foo': 'bar'} where 'foo' is the variable and 'bar' the substitution value).
        @rtype:     string
        @return:    CLI command
        """
        res_cmd = []
        for cmd_part in CliCommand._commands[name]:
            if isinstance(cmd_part, string.Template):
                res_cmd.append(cmd_part.substitute(subst))
            else:
                res_cmd.append(cmd_part)
        return res_cmd


class CliCommandTest(unittest.TestCase):
    def test_get_cli_command(self):
        """
        Must return CLI command
        """
        actual = CliCommand.get("summain", {'manifest_file': 'foo', 'package_dir': 'bar'})
        self.assertTrue(actual, "['/usr/bin/summain', '-c', 'SHA256', '-c', 'MD5', '--exclude=Ino,Dev,Uid,Username,Gid,Group,Nlink,Mode', '--output', 'foo', 'bar']")


if __name__ == '__main__':
    unittest.main()
