"""
Load and access custom properties from ~/.pyfu/pyfu.properties
"""

import os

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


properties_file_path = os.path.expanduser("~") + '/.pyfu/pyfu.properties'
try:
    properties = __read_properties(properties_file_path)
except IOError as e:
    properties = {}


def get(key, default=None):
    return properties.get(key, default)


def get_as_nested_map():
    nested_map = {}
    for key in properties.keys():
        maputil.add_nested(nested_map, key, properties[key])
    return nested_map


def get_or_die(key):
    if key not in properties:
        print("key '{}' not found in properties file '{}'".format(key, properties_file_path))
        exit(1)
    return properties[key]
