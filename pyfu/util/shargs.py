"""
This script exists as a glue to have Python scripts execute BASH scripts and have the Python command arguments
passed along to the BASH script.
"""

import sys

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


def as_string(args=sys.argv[1:]):
    """Converts array of arguments into a string, like so:
    [foo, 'bar 2', 3, '"bazz 4"'] --> foo "bar 2" 3 ""bazz 4""
    """
    return ' '.join(_add_quotes(args))


def _add_quotes(args=sys.argv[1:]):
    """Convert sys.argv into an array of arguments and if any argument has a space

    Returns:
        The same array of strings, but each arg with a space is surrounded with double quotes.
    """
    return ['"%s"' % a if _should_quote(a) else a for a in args]


def _should_quote(arg):
    return ' ' in arg
