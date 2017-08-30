import json
import os
import requests
import subprocess
import time

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'
__osver__ = '*nix'


# Tomcat healthcheck: curl -XGET curl --anyauth -u admin: "http://localhost:8800/manager/html"

class Server(object):
    """Holder of all information needed to start/stop/monitor an app server."""

    def __init__(self, name=None, path=None, executable=None, type=None, logpath=None):
        self.name = name
        self.path = path  # should always end with /
        self.executable = executable
        self.type = type
        self.logpath = logpath

    def start(self):
        """Start the app only if not running."""
        if self.running():
            return False
        else:
            logfile = open(self.logpath, 'w')
            if self.type == 'springboot':
                subprocess.Popen('java -jar -Xms50m -Xmx50m ' + self.path + self.executable, shell=True, stdout=logfile)
            elif self.type == 'tomcat':
                subprocess.Popen('sh ' + self.path + self.executable, shell=True, stdout=logfile)
            return True

    def stop(self):
        """Stop the app if it's running."""
        if self.running():
            subprocess.call(['kill', '-9', self._pid()])
            time.sleep(1)
            return True
        return False

    def restart(self):
        """Restart the app."""
        self.stop()
        return self.start()

    def status(self):
        """Get the status of the app (running or not)."""
        if self.running():
            return True, 'running'
        else:
            return False, 'not running'

    def running(self):
        """Test if the server is running."""
        if self._pid():
            return True
        else:
            return False

    def catlog(self):
        """Get the contents of the app log."""
        return subprocess.Popen('cat ' + self.logpath, stdout=subprocess.PIPE,
                                shell=True).stdout.read().decode('utf8')

    def lesslog(self):
        """Show the app's log using 'less' program."""
        subprocess.call(['less', self.logpath])

    def taillog(self):
        """Tail the app's log file."""
        subprocess.call(['tail', '-f', self.logpath])

    def apps(self):
        """Return the wars in the webapps directory."""
        if self.type == 'springboot':
            return self.executable
        else:
            webapps = subprocess.Popen('ls -1 ' + self.path + 'webapps |grep war |sort', stdout=subprocess.PIPE,
                                       shell=True).stdout.read().decode('utf8').strip()
            return '(none)' if not webapps else webapps

    def healthcheck(self):
        """Health check each app on the server."""
        # TODO clean this up
        apps = sorted(self.apps().splitlines())
        all_results = []
        for app in apps:
            name = app
            if '.' in app:
                name = app[0:app.rfind(".")]
            url = 'http://localhost:8080/' + name + '/healthcheck/quick'
            all_results.append(self._health(name, url))
        return '\n    '.join(all_results)

    def _health(self, name, url):
        try:
            response = requests.get(url)
            if response.ok:
                results = requests.get(url).text
                health = json.loads(results)
                if 'appVersion' in health:
                    return name + ' (' + health['appVersion'] + ')'
        except Exception as e:
            pass
        return name + ' (?)'

    def deploy(self, artifact_path, artifact_name):
        """Deploy an artifact to the app server."""
        if self.type == 'springboot':
            # TODO: implement
            raise NotImplementedError("I don't know how to do what you asked.")
        else:
            if self.running():
                self.stop()
            # subprocess.Popen(
            #     'rm -rf ' + artifact_path + ' ' + self.path + 'webapps/' + artifact_name[0:artifact_name.rfind(".")],
            #     shell=True)
            subprocess.Popen('cp ' + artifact_path + ' ' + self.path + 'webapps/' + artifact_name, shell=True)
            while True:
                processes = subprocess.Popen('pgrep -lf "' + self._id() + '"', stdout=subprocess.PIPE,
                                             shell=True).stdout.read().decode('utf8')
                if ' cp ' not in processes:
                    break
                time.sleep(1)
            return self.start()

    def _pid(self):
        """Get the process ID of the app, if it's running."""
        self.pid = subprocess.Popen('pgrep -f "' + self._id() + '"', stdout=subprocess.PIPE,
                                    shell=True).stdout.read().decode('utf8')
        self.pid = ' '.join(self.pid.splitlines())
        return self.pid

    def _id(self):
        """Get the ID of this app that can be used to identify the process."""
        return self.path if self.path.endswith(os.path.sep) else self.path + os.path.sep


class Tomcat(Server):
    def __init__(self, *args, **kwargs):
        super(Tomcat, self).__init__(*args, **kwargs)
        if not self.path.endswith('/'):
            self.path += '/'
        if not self.logpath:
            self.logpath = self.path + 'logs/catalina.out'
        if not self.executable:
            self.executable = 'bin/startup.sh'
        if not self.type:
            self.type = 'tomcat'
