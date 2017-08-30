"""
Convenience methods for reading/writing to console.
"""

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


class Technicolor:
    """ For printing to BASH shell in technicolor. """
    HEADER = '\033[95m'
    GRAY = '\033[2m'
    GREY = '\033[2m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'


def putc(text='', color=None, bold=False, italic=False, underline=False):
    prefix = ''
    if bold:
        prefix += Technicolor.BOLD
    if italic:
        prefix += Technicolor.ITALIC
    if underline:
        prefix += Technicolor.UNDERLINE
    if not color:
        print(prefix + text + Technicolor.ENDC)
    else:
        color = color.lower()
        if color == 'red':
            print(prefix + Technicolor.FAIL + text + Technicolor.ENDC)
        elif color == 'yellow':
            print(prefix + Technicolor.WARNING + text + Technicolor.ENDC)
        elif color == 'green':
            print(prefix + Technicolor.OKGREEN + text + Technicolor.ENDC)
        elif color == 'gray' or color == 'grey':
            print(prefix + Technicolor.GRAY + text + Technicolor.ENDC)
        elif color == 'blue':
            print(prefix + Technicolor.OKBLUE + text + Technicolor.ENDC)
        else:
            print(prefix + text + Technicolor.ENDC)
