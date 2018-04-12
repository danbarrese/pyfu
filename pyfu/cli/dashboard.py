import sys

from pyfu.util import props
from pyfu.ui import ui

properties = props.get_as_nested_map().get('dashboard', None)

if len(sys.argv) == 1:
    dashboards = []
    if properties:
        dashboards = sorted(properties.keys())
    print("Which dashboard? " + str(dashboards))
    exit(1)

name = sys.argv[1]
dashboard = ui.Dashboard(properties[name])
dashboard.run()
