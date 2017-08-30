import argparse
import os
import subprocess

from pyfu.appmgr import Server
from pyfu import ioutils
from pyfu import appmgr
from pyfu.util import sig, props

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'
__osver__ = '*nix'

possible_actions = "start, stop, restart, status, log, less, tail, cat, path, apps, deploy"

sig.handle_ctrl_c()


def usage_and_die():
    print("usage examples...")
    print("1. <server> <action> [<action> <action> ...]")
    print("2. <server> deploy <artifact_path> [artifact_name]")
    print()
    print("actions: " + possible_actions)
    exit(1)


class Gateway(Server):
    def __init__(self, *args, **kwargs):
        super(Gateway, self).__init__(*args, **kwargs)

    def apps(self):
        cmd = 'cat ~/portal/gateway.properties |grep -v "^\s*$" |grep -v "^\s*#.*" |cut -d= -f1 |cut -d. -f3 |sort -u',
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).stdout.read().decode('utf8').strip()


all_servers = []
appmgr_props = props.get_as_nested_map().get('appmgr', {})
for name, args in appmgr_props.items():
    if name == 'gateway':
        all_servers.append(Gateway(name=name, **args))
    else:
        all_servers.append(appmgr.Server(name=name, **args))

parser = argparse.ArgumentParser(description='App Manager (supply single arg of "help")')
args, unknown_args = parser.parse_known_args()

artifact_path = None
artifact_name = None
servers = []
actions = []
if len(unknown_args) == 0:
    actions = ['status']
    servers = [s.name for s in all_servers]
elif len(unknown_args) < 2:
    usage_and_die()
elif unknown_args[1] == 'deploy' and len(unknown_args) < 3:
    usage_and_die()
elif unknown_args[1] == 'deploy':
    servers = [unknown_args[0].lower()]
    actions = [unknown_args[1]]
    artifact_path = os.path.abspath(unknown_args[2])
    if len(unknown_args) > 3:
        artifact_name = unknown_args[3]
else:
    servers = [unknown_args[0].lower()]
    actions = [a.lower() for a in unknown_args[1:]]

matches = all_servers if servers == ['all'] else [s for s in all_servers if s.name in servers]

if not matches:
    print("Unknown server name(s): " + str(servers))

for server in matches:
    for action in actions:
        if action not in possible_actions:
            print("unknown action: " + action)
            continue
        if action == 'start':
            if server.start():
                print(server.name + ': starting...')
            else:
                running, msg = server.status()
                if running:
                    ioutils.putc('[ ✓ running     ] ' + server.name, 'green')
                else:
                    ioutils.putc('[ ✗ not running ] ' + server.name, 'red')
        elif action == 'stop':
            if server.stop():
                print(server.name + ': stopped')
            else:
                running, msg = server.status()
                if running:
                    ioutils.putc('[ ✓ running     ] ' + server.name, 'green')
                else:
                    ioutils.putc('[ ✗ not running ] ' + server.name, 'red')
        elif action == 'restart':
            if server.restart():
                print(server.name + ': starting...')
            else:
                running, msg = server.status()
                if running:
                    ioutils.putc('[ ✓ running     ] ' + server.name, 'green')
                else:
                    ioutils.putc('[ ✗ not running ] ' + server.name, 'red')
        elif action == 'status':
            running, msg = server.status()
            if running:
                ioutils.putc('[ ✓ running     ] ' + server.name, 'green')
                ioutils.putc('    ' + server.healthcheck(), 'gray')
            else:
                ioutils.putc('[ ✗ not running ] ' + server.name, 'red')
        elif action == 'log' or action == 'less':
            if len(matches) != 1:
                print("cannot view more than 1 log")
                exit(1)
            matches[0].lesslog()
        elif action == 'tail':
            if len(matches) != 1:
                print("cannot tail more than 1 log")
                exit(1)
            matches[0].taillog()
        elif action == 'cat':
            if len(matches) != 1:
                print("cannot cat more than 1 log")
                exit(1)
            print(matches[0].catlog())
        elif action == 'path':
            print(server.path)
        elif action == 'apps':
            print(server.apps())
        elif action == 'deploy':
            if server.deploy(artifact_path=artifact_path, artifact_name=artifact_name):
                print(server.name + ': starting...')
            else:
                print(server.name + ': not sure what happened...')
