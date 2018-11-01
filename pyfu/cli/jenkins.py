import argparse
import datetime
import json
import os
import requests
import time
from sys import exit

from pyfu import ioutils
from pyfu.util import props

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


def log(s):
    print(s)


class BuildResult(object):
    def __init__(self, success, groupId, artifactId, version):
        self.success = success
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version


class JenkinsProject(object):
    LAST_BUILD = '/lastBuild/api/json'
    BUILD = '/build?delay=0sec'
    M2RELEASE = '/m2release/submit'
    MVN_ARTIFACTS = '/lastBuild/mavenArtifacts/api/json'
    LAST_BUILD_OUTPUT = '/lastBuild/logText/progressiveText'
    params = {'parameter': {}}

    def __init__(self, baseUrl, name):
        self.baseUrl = baseUrl
        self.name = name

    def isBuildInProgress(self):
        [status, response] = self.lastBuild()
        if status == 404:
            raise Exception("Jenkins project not found.")
        return response['building']

    def lastBuildNumber(self):
        [status, response] = self.lastBuild()
        if status == 404:
            raise Exception("Jenkins project not found.")
        return response['number']

    def lastBuild(self):
        return self._apiGet(projectName, self.LAST_BUILD)

    def addParam(self, name, value):
        j = {'name': name, 'value': value}
        if not self.params:
            self.params = {}
        if not self.params['parameter']:
            self.params['parameter'] = []
        self.params['parameter'].append(j)

    def buildSnapshot(self):
        buildParams = '&json=' + json.dumps(self.params)
        url = self.baseUrl + self.name + self.BUILD
        requests.post(url=url, params=buildParams)

    def release(self, releaseVersion, branch='develop'):
        devVersion = self._nextSnapshotVersion(releaseVersion)
        releaseParams = 'versioningMode=specify_version'
        releaseParams += '&releaseVersion=' + releaseVersion
        releaseParams += '&developmentVersion=' + devVersion
        releaseParams += '&scmUsername='
        releaseParams += '&scmPassword='
        releaseParams += '&scmCommentPrefix=[maven-release-plugin]'
        if branch:
            releaseParams += '&name=branchName'
            releaseParams += '&value=' + branch
        releaseParams += '&Submit=Schedule Maven Release Build'
        j = {'releaseVersion': releaseVersion, 'developmentVersion': devVersion, 'isDryRun': False}
        if branch:
            j['parameter'] = {}
            j['parameter']['name'] = 'branchName'
            j['parameter']['value'] = branch
        releaseParams += '&json=' + json.dumps(j)
        log(devVersion)
        log(releaseParams)
        raise Exception("releases are disabled until I implement default release parameters")
        self._apiPost(projectName, self.M2RELEASE, params=releaseParams)

    def awaitJobStart(self, projectName, oldBuildNumber, delay=1.0):
        """ Polls url looking for a different build number. """
        newBuildNumber = oldBuildNumber
        while newBuildNumber == oldBuildNumber:
            time.sleep(delay)
            [status, response] = self._apiGet(projectName, self.LAST_BUILD)
            if status != 404:
                newBuildNumber = response['number']
        return newBuildNumber

    def awaitJobComplete(self, projectName, buildNum=0, delay=10.0, taillog=False):
        """ Polls project's API looking for the last build to be complete. """
        homeDir = os.path.expanduser("~")
        if buildNum is 0:
            with open("{homeDir}/.pyfu/jenkins/{projectName}.{buildNum}".format(**locals()), 'w+') as logFile:
                logFile.write("")
        line = 0
        buildInProgress = True
        while buildInProgress:
            time.sleep(delay)
            [status, response] = self._apiGet(projectName, self.LAST_BUILD)
            if status != 404:
                buildInProgress = response['building']
            log = self._apiLog(projectName)
            lines = log.splitlines()
            newLines = lines[line:]
            line = len(lines)
            if len(newLines) > 0:
                newOutput = '\n'.join(newLines)
                if taillog:
                    ioutils.putc(newOutput, color='gray', italic=True)
                with open("{homeDir}/.pyfu/jenkins/{projectName}.{buildNum}".format(**locals()), 'a+') as logFile:
                    logFile.write(newOutput + '\n')

        [status, response] = self._apiGet(projectName, self.LAST_BUILD)
        result = response['result']
        success = result.upper() == 'SUCCESS'
        groupId = None
        artifactId = None
        version = None

        if success:
            [status, response] = self._apiGet(projectName, self.MVN_ARTIFACTS)
            artifactId = response['moduleRecords'][0]['mainArtifact']['artifactId']
            groupId = response['moduleRecords'][0]['mainArtifact']['groupId']

            response = self._apiLog(projectName).splitlines()
            version = "(?)"
            for line in response:
                if "Installing" in line:
                    v = line
                    v = line[0:line.rfind("/")]
                    v = v[v.rfind("/") + 1:len(v)]
                    version = v
                    break
        return BuildResult(success=success, groupId=groupId, artifactId=artifactId, version=version)

    def _curl(self, url):
        resp = requests.get(url)
        respStatus = resp.status_code
        respText = json.loads("{}")
        if resp.ok:
            respText = json.loads(resp.text)
        return respStatus, respText

    def _curlText(self, url):
        resp = requests.get(url)
        respStatus = resp.status_code
        respText = ''
        if resp.ok:
            respText = resp.text
        return respStatus, respText

    def _apiLog(self, projectName):
        url = self.baseUrl + projectName + self.LAST_BUILD_OUTPUT
        [status, response] = self._curlText(url)
        return response

    def _apiGet(self, projectName, action):
        return self._curl(self.baseUrl + projectName + action)

    def _apiPost(self, projectName, action, params=''):
        url = BASE_JENKINS_URL + projectName + action
        requests.post(url=url, params=params)

    def _nextSnapshotVersion(self, releaseVersion):
        vtokens = releaseVersion.split('.')
        vtokens[-1] = str(int(vtokens[-1]) + 1) + '-SNAPSHOT'
        nextSnapshotVersion = '.'.join(vtokens)
        return nextSnapshotVersion

    def _autoGetNextReleaseVersions(self, current_version):
        vtokens = current_version.split('.')
        vtokens[-1] = str(int(vtokens[-1]) + 1)
        releaseVersion = '.'.join(vtokens)
        vtokens[-1] = str(int(vtokens[-1]) + 1) + '-SNAPSHOT'
        devVersion = '.'.join(vtokens)
        return releaseVersion, devVersion


BASE_JENKINS_URL = props.get_or_die(key='jenkins.url')
if not BASE_JENKINS_URL.endswith('/'):
    BASE_JENKINS_URL += '/'
DEFAULT_GROUP_ID = props.get(key='mvnrepo.default-group-id', default=None)

parser = argparse.ArgumentParser(description='Automate Jenkins build server build02 via REST API')
parser.add_argument('-p', type=str, nargs=1, required=True,
                    dest='projectName', default=[None],
                    help='Jenkins project name.')
parser.add_argument('-l', dest='showLog', action='store_true', default=False,
                    help='Poll output log of Jenkins job.')
parser.add_argument('--branch', type=str, nargs=1, required=False, dest='branch', default=['develop'],
                    help='branchName build parameter')
buildRelease = parser.add_mutually_exclusive_group()
buildRelease.add_argument('-b', dest='build', action='store_true', help='Build project')
buildRelease.add_argument('-r', dest='release', action='store_true', help='Release project')
buildRelease.set_defaults(boolean=False)
buildRelease.required = True
versionGroup = parser.add_argument_group()
versionGroup.add_argument('-v', metavar='RELEASE_VERSION', type=str, nargs=1, required=False,
                          dest='releaseVersion', default=[None],
                          help='Release version.  Only applicable if doing release.')
versionGroup.required = False
args = parser.parse_args()
projectName = args.projectName[0]
build = args.build
release = args.release
releaseVersion = args.releaseVersion[0]
showLog = args.showLog
branch = args.branch[0]

if not projectName:
    ioutils.putc("[ FAIL ] Project name cannot be empty", color='red', bold=True)
    exit(1)

if release and not releaseVersion:
    ioutils.putc("[ FAIL ] If you want to release, you must specify a version.", color='red', bold=True)
    exit(1)

# initialize log directory
homeDir = os.path.expanduser("~")
if not os.path.exists('{homeDir}/.pyfu'.format(**locals())):
    os.mkdir('{homeDir}/.pyfu'.format(**locals()))

jenkinsProject = JenkinsProject(baseUrl=BASE_JENKINS_URL, name=projectName)

# make sure build is not in progress
log("Getting previous build number.")
if jenkinsProject.isBuildInProgress():
    ioutils.putc("[ FAIL ] Build is already in progress!", color='red', bold=True)
    exit(1)

# get previous build number
previousBuildNumber = jenkinsProject.lastBuildNumber()

# set params
jenkinsProject.addParam(name="branchName", value=branch)

if build:
    log("Building {projectName}.".format(**locals()))
    jenkinsProject.buildSnapshot()
elif release:
    log("Releasing {projectName}.".format(**locals()))
    jenkinsProject.release(releaseVersion)

log("Waiting for job to start.")
buildNum = jenkinsProject.awaitJobStart(projectName, previousBuildNumber)
log("Job started.  Waiting for job to complete.")
buildResult = jenkinsProject.awaitJobComplete(projectName, buildNum=buildNum, taillog=showLog)

if buildResult.success:
    result = '[ OK ] {buildResult.groupId} {buildResult.artifactId} {buildResult.version} released'.format(**locals())
    ioutils.putc(result, color='green', bold=True)
    with open("{homeDir}/.pyfu/jenkins/all.log".format(**locals()), 'a+') as logFile:
        logFile.write(result + '\n')
else:
    result = '[ FAILED ] {projectName}'.format(**locals())
    ioutils.putc(result, color='red', bold=True)
    with open("{homeDir}/.pyfu/jenkins/all.log".format(**locals()), 'a+') as logFile:
        logFile.write(str(datetime.datetime.now()) + ": " + result + '\n')
