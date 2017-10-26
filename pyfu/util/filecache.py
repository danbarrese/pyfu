"""
Loads a cached version of a file.
"""

import os
import time

from pyfu.util import props

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'

timeout_sec = int(props.get('filecache.timeout.sec', 60 * 10))


def available(filename):
    if not filename:
        return False
    if timeout_sec <= 0:
        return False
    try:
        path = os.path.expanduser("~") + '/.pyfu/cache/' + filename
        modified = os.path.getmtime(path)
        return modified >= (time.time() - timeout_sec)
    except OSError as e:
        return False


def get(filename):
    if not filename:
        return False
    try:
        path = os.path.expanduser("~") + '/.pyfu/cache/' + filename
        lines = ''.join([line.rstrip('\n') for line in open(path)])
        return lines
    except OSError as e:
        return False


def put(filename, contents):
    try:
        home = os.path.expanduser("~")
        path = home + '/.pyfu/cache/' + filename
        try:
            os.mkdir(home + '/.pyfu')
            os.mkdir(home + '/.pyfu/cache')
        except Exception as e:
            pass
        with open(path, "w") as myfile:
            myfile.write(contents)
    except Exception as e:
        pass
