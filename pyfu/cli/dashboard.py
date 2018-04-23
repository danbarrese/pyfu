import sys
import os
from sys import exit

from pyfu.util import props
from pyfu.ui import ui

properties_path = os.path.expanduser("~") + '/.dashboard/dashboard.properties'
properties = props.get_as_nested_map(properties_path).get('dashboard', None)

if len(sys.argv) == 1:
    dashboards = []
    if properties:
        dashboards = sorted(properties.keys())
    print("Which dashboard? " + str(dashboards))
    exit(1)

name = sys.argv[1]
dashboard = ui.Dashboard(properties[name])
dashboard.run()
