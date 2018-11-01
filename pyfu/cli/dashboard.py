import sys
import os
from sys import exit
import yaml

from pyfu.ui import ui

yaml_path = os.path.expanduser("~") + '/.dashboard/dashboard.yaml'
if not os.path.isfile(yaml_path):
    print("No yaml file: " + yaml_path)
    exit(1)
yaml_contents = '\n'.join([line.rstrip('\n') for line in open(yaml_path)])
if not yaml_contents:
    print("Your yaml file is empty: " + yaml_path)
    exit(1)
properties = yaml.load(yaml_contents)

if len(sys.argv) == 1:
    dashboards = []
    if properties:
        dashboards = [d['name'] for d in properties['dashboards']]
        dashboards = sorted(dashboards)
    print("Which dashboard? " + str(dashboards))
    exit(1)

name = sys.argv[1]
d = [d for d in properties['dashboards'] if d['name'] == name][0]
dashboard = ui.Dashboard(d, name)
dashboard.run()
