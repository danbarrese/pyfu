import columnize

__author__ = 'Dan Barrese'
__pythonver__ = '3.6'

def asdf(lines):
    return columnize.columnize(lines)
    
print(asdf("abc a\nx xyz"))
