"""
Handles ctrl-C by just doing exit(0).
"""

import signal
import sys

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


def __signal_handler(signal, frame):
    sys.exit(0)


def handle_ctrl_c():
    signal.signal(signal.SIGINT, __signal_handler)
