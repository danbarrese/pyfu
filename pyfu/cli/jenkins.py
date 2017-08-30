import argparse
import datetime
import json
import os
import requests
import time

from pyfu import ioutils
from pyfu import nexus as mvnrepo
from pyfu.util import props

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


class jenkins_endpoint:
    """ Available Jenkins endpoints. """
    LAST_BUILD = '/lastBuild/api/json'
    BUILD = '/build?delay=0sec'
    M2RELEASE = '/m2release/submit'
    MVN_ARTIFACTS = '/lastBuild/mavenArtifacts/api/json'
    LAST_BUILD_OUTPUT = '/lastBuild/logText/progressiveText'


BASE_JENKINS_URL = props.get_or_die('jenkins.url')
if not BASE_JENKINS_URL.endswith('/'):
    BASE_JENKINS_URL += '/'
DEFAULT_GROUP_ID = props.get('mvnrepo.default-group-id', None)


def make_release_dev_versions(current_version):
    vtokens = current_version.split('.')
    vtokens[-1] = str(int(vtokens[-1]) + 1)
    release_version = '.'.join(vtokens)
    vtokens[-1] = str(int(vtokens[-1]) + 1) + '-SNAPSHOT'
    development_version = '.'.join(vtokens)
    return release_version, development_version


def _curl(url):
    resp = requests.get(url)
    resp_status = resp.status_code
    resp_text = json.loads("{}")
    if resp.ok:
        resp_text = json.loads(resp.text)
    return resp_status, resp_text


def _curl_text(url):
    resp = requests.get(url)
    resp_status = resp.status_code
    resp_text = ''
    if resp.ok:
        resp_text = resp.text
    return resp_status, resp_text


def api_log(project_name):
    url = BASE_JENKINS_URL + project_name + jenkins_endpoint.LAST_BUILD_OUTPUT
    [status, response] = _curl_text(url)
    return response


def api_get(project_name, action):
    return _curl(BASE_JENKINS_URL + project_name + action)


def api_post(project_name, action, params=''):
    url = BASE_JENKINS_URL + project_name + action
    requests.post(url=url, params=params)


def await_job_start(project_name, old_build_number, delay=1.0):
    """ Polls url looking for a different build number. """
    new_build_number = old_build_number
    while new_build_number == old_build_number:
        time.sleep(delay)
        [status, response] = api_get(project_name, jenkins_endpoint.LAST_BUILD)
        if status != 404:
            new_build_number = response['number']
    return new_build_number


def await_job_complete(project_name, build_num=0, delay=10.0, taillog=False):
    """ Polls project's API looking for the last build to be complete. """
    home_dir = os.path.expanduser("~")
    if build_num is 0:
        with open("{home_dir}/.pyfu/jenkins/{project_name}.{build_num}".format(**locals()), 'w+') as log_file:
            log_file.write("")
    line = 0
    build_in_progress = True
    while build_in_progress:
        time.sleep(delay)
        [status, response] = api_get(project_name, jenkins_endpoint.LAST_BUILD)
        if status != 404:
            build_in_progress = response['building']
        log = api_log(project_name)
        lines = log.splitlines()
        new_lines = lines[line:]
        line = len(lines)
        if len(new_lines) > 0:
            new_output = '\n'.join(new_lines)
            if taillog:
                ioutils.putc(new_output, color='gray', italic=True)
            with open("{home_dir}/.pyfu/jenkins/{project_name}.{build_num}".format(**locals()), 'a+') as log_file:
                log_file.write(new_output + '\n')


def perform_build(project_name, branch):
    j = {'parameter': {'name': 'branchName', 'value': branch}}
    release_params = '&json=' + json.dumps(j)
    api_post(project_name, jenkins_endpoint.BUILD, params=release_params)


def perform_m2release(project_name, branch, release_version=None, dev_version=None):
    release_params = ""
    if dev_version:
        release_params = 'versioningMode=specify_version'
        release_params += '&releaseVersion=' + release_version
        release_params += '&developmentVersion=' + dev_version
        release_params += '&scmUsername='
        release_params += '&scmPassword='
        release_params += '&scmCommentPrefix=[maven-release-plugin]'
        if branch:
            release_params += '&name=branchName'
            release_params += '&value=' + branch
        release_params += '&Submit=Schedule Maven Release Build'
        j = {'releaseVersion': release_version, 'developmentVersion': dev_version, 'isDryRun': False}
        if branch:
            j['parameter'] = {}
            j['parameter']['name'] = 'branchName'
            j['parameter']['value'] = branch
        release_params += '&json=' + json.dumps(j)
    else:
        release_params = 'versioningMode=auto'
    api_post(project_name, jenkins_endpoint.M2RELEASE, params=release_params)


parser = argparse.ArgumentParser(description='Automate Jenkins build server build02 via REST API')
parser.add_argument('-p', type=str, nargs=1, required=True,
                    dest='project_name', default=[None],
                    help='Jenkins project name.')
parser.add_argument('--mvntree', dest='mvntree', action='store_true', default=False,
                    help='Show project dependencies after build/release.')
parser.add_argument('-l', dest='show_log', action='store_true', default=False,
                    help='Poll output log of Jenkins job.')
parser.add_argument('-a', type=str, nargs=1, required=False,
                    dest='aid', default=[None],
                    help='Artifact ID, for retrieving new build numbers automatically.')
parser.add_argument('-g', type=str, nargs=1, required=False,
                    dest='gid', default=[DEFAULT_GROUP_ID],
                    help='Group ID, for retrieving new build numbers automatically.')
parser.add_argument('--branch', type=str, nargs=1, required=False, dest='branch', default=['develop'],
                    help='branchName build parameter')
build_release = parser.add_mutually_exclusive_group()
build_release.add_argument('-b', dest='build', action='store_true', help='Build project')
build_release.add_argument('-r', dest='release', action='store_true', help='Release project')
build_release.set_defaults(boolean=False)
build_release.required = True
version_group = parser.add_argument_group()
version_group.add_argument('--v1', metavar='RELEASE_VERSION', type=str, nargs=1, required=False,
                           dest='release_version', default=[None],
                           help='Release version.  Only applicable if doing release.')
version_group.add_argument('--v2', metavar='DEV_VERSION', type=str, nargs=1, required=False,
                           dest='dev_version', default=[None],
                           help='Development version.  Only applicable if doing release.')
version_group.required = False
args = parser.parse_args()
project_name = args.project_name[0]
build = args.build
release = args.release
release_version = args.release_version[0]
dev_version = args.dev_version[0]
do_mvntree = args.mvntree
show_log = args.show_log
gid = args.gid[0]
aid = args.aid[0]
branch = args.branch[0]

if not project_name:
    ioutils.putc("[ FAIL ] Project name cannot be empty", color='red', bold=True)
    exit(1)

if release and (bool(release_version) != bool(dev_version)):
    ioutils.putc("[ FAIL ] If you supply a release version or dev version, you must supply both.", color='red',
                 bold=True)
    exit(1)

if release and not aid and (not bool(release_version) or not bool(dev_version)):
    ioutils.putc(
        "[ FAIL ] If you don't supply release/dev versions, you must supply an artifactId so I can figure out the next version to release.",
        color='red', bold=True)
    exit(1)

if release and not release_version:
    ver = None
    try:
        ver = mvnrepo.latest_version(group_id=gid, artifact_id=aid)
    except FileNotFoundError as e:
        ioutils.putc(
            "[ FAIL ] The artifactId you supplied can't be found in Nexus.  Maybe try also providing the groupId?",
            color='red', bold=True)
        exit(1)
    release_version, dev_version = make_release_dev_versions(ver)
    print('Current version of {gid}.{aid} is {ver}'.format(**locals()))
    print('Releasing version {release_version}'.format(**locals()))

# initialize log directory
home_dir = os.path.expanduser("~")
if not os.path.exists('{home_dir}/.pyfu'.format(**locals())):
    os.mkdir('{home_dir}/.pyfu'.format(**locals()))

# get previous build number
# make sure build is not in progress
print("Getting previous build number.")
previous_build_number = 0
[status, response] = api_get(project_name, jenkins_endpoint.LAST_BUILD)
build_in_progress = False
if status != 404:
    build_in_progress = response['building']
    previous_build_number = response['number']
if build_in_progress:
    ioutils.putc("[ FAIL ] Build is already in progress!", color='red', bold=True)
    exit(1)

if build:
    print("Building {project_name}.".format(**locals()))
    perform_build(project_name=project_name, branch=branch)
elif release:
    print("Releasing {project_name}.".format(**locals()))
    perform_m2release(project_name=project_name, release_version=release_version, dev_version=dev_version,
                      branch=branch)

print("Waiting for job to start.")
build_num = await_job_start(project_name, previous_build_number)
print("Job started.  Waiting for job to complete.")
await_job_complete(project_name, build_num=build_num, taillog=show_log)

# job is done, was it successful?
print("Job is done.  Getting results.")
[status, response] = api_get(project_name, jenkins_endpoint.LAST_BUILD)
result = response['result']
success = result.upper() == 'SUCCESS'
last_build_results = response

if success:
    [status, response] = api_get(project_name, jenkins_endpoint.MVN_ARTIFACTS)
    artifact_id = response['moduleRecords'][0]['mainArtifact']['artifactId']
    group_id = response['moduleRecords'][0]['mainArtifact']['groupId']

    response = api_log(project_name).splitlines()
    version = "(?)"
    for line in response:
        if "Installing" in line:
            v = line
            v = line[0:line.rfind("/")]
            v = v[v.rfind("/") + 1:len(v)]
            version = v
            break
    result = '[ OK ] {group_id} {artifact_id} {version} released'.format(**locals())
    ioutils.putc(result, color='green', bold=True)
    with open("{home_dir}/.pyfu/jenkins/all.log".format(**locals()), 'a+') as log_file:
        log_file.write(result + '\n')

    # get artifact dependency tree for the project
    if do_mvntree:
        print("Building MVN dependency tree.")
        try:
            svn_url = last_build_results['changeSet']['revisions'][0]['module']
            # TODO: need to make a mvntree module.
            mvntree = os.popen("mvntree -s {svn_url}".format(**locals())).read()
            print(str(mvntree))
        except Exception as e:
            print("Could not build mvntree.")
            pass
else:
    result = '[ FAILED ] {project_name}'.format(**locals())
    ioutils.putc(result, color='red', bold=True)
    with open("{home_dir}/.pyfu/jenkins/all.log".format(**locals()), 'a+') as log_file:
        log_file.write(str(datetime.datetime.now()) + ": " + result + '\n')
