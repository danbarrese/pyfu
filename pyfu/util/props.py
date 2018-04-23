"""
Load and access custom properties from ~/.pyfu/pyfu.properties
"""

import os
from sys import exit

from pyfu.util import maputil

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


def __read_properties(path):
    lines = []
    for line in open(os.path.join(os.path.dirname(__file__), path)):
        if line:
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line.strip().split('='))
    return dict(lines)


def __prep_properties(path):
    if path not in all_properties:
        try:
            all_properties[path] = __read_properties(path)
        except IOError as e:
            all_properties[path] = {}


default_path = os.path.expanduser("~") + '/.pyfu/pyfu.properties'
all_properties = {}
__prep_properties(default_path)


def get(key, path=default_path, default=None):
    __prep_properties(path)
    return all_properties[path].get(key, default)


def get_as_nested_map(path=default_path):
    __prep_properties(path)
    nested_map = {}
    for key in all_properties[path].keys():
        maputil.add_nested(nested_map, key, all_properties[path][key])
    return nested_map


def get_or_die(key, path=default_path):
    __prep_properties(path)
    if key not in all_properties[path]:
        print(
            "A property named '{}' was not found in the properties file located at '{}'.  You will have to add it yourself.  End of line.".format(
                key, path))
        exit(1)
    return all_properties[path][key]
