#!/usr/bin/env python
# coding=UTF-8
__author__ = "Jan Rörden, Roman Graf, Sven Schlarb"
__copyright__ = "Copyright 2015, The E-ARK Project"
__license__ = "GPL"
__version__ = "0.0.1"

class XMLSchemaNotFound(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)