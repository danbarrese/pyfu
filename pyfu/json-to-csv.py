import json
import sys

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'

lines = [line.rstrip('\n') for line in open(sys.argv[1])]
j = json.loads(' '.join(lines))
first = j['result'][0]
print(','.join(first.keys()))
print()
for entry in j['result']:
    row = ''
    for key in sorted(entry):
        row += '"' + entry[key] + '",'
    print(row[:-1])
