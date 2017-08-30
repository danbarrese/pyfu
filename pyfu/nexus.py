"""
Makes REST calls to Nexus repo.
"""

import argparse
import json
import shlex
import datetime
import urllib.error
import requests
import wget
from xml.etree import ElementTree as ET

from pyfu.util import props

__author__ = 'Dan Barrese'
__pythonver__ = '3.5'

NEXUS_URL = props.get_or_die('mvnrepo.url').rstrip('/')
DEFAULT_GROUP_ID = props.get('mvnrepo.default-group-id', None)


class Jsonify(object):
    def to_json(self, indent='    '):
        return json.dumps(self, default=lambda o: o.__dict__, indent=indent, sort_keys=False)


class ArtifactInfo(object):
    """Holder of extension & classifier data."""

    def __init__(self, ext, classifier):
        self.ext = ext
        self.classifier = classifier


class MavenMetadata(object):
    def __init__(self, group_id, artifact_id, repo, versions):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.repo = repo
        self.versions = versions

    def latest_version(self):
        return self.versions[-1] if self.versions else None

    def latest_n_versions(self, n):
        return reversed(self.versions[-n:]) if self.versions else []


class Version(Jsonify):
    def __init__(self, version, uploaded=None):
        self.version = version
        self.uploaded = uploaded

    def __str__(self):
        if self.uploaded:
            return '{self.version} ({self.uploaded})'.format(**locals())
        else:
            return str(self.version)


class Versions(Jsonify):
    def __init__(self, repo, group_id, artifact_id, versions=None):
        self.repo = repo
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.versions = versions
        if not self.versions:
            self.versions = []

    def __str__(self):
        s = ''
        for v in self.versions:
            s += '{self.group_id}: {self.artifact_id}: '.format(**locals())
            s += str(v)
            s += '\n'
        return s[:-1]

    def add(self, version):
        self.versions.append(version)


def nexus_ver_cli(s=None):
    """Get artifact version info from Maven repo (Nexus).
    This is a CLI version of the nexus_ver method, the difference in this method
    being you call it with a single string which is then passed through a CLI
    arg parser.

    Args:
        s: Single string containing all CLI program args.
           ex: '-vsa common-domain-api -c 3'
    Returns:
        Versions object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('-s', dest='snapshots', action='store_true')
    parser.add_argument('-g', dest='gid', type=str, nargs=1, default=[DEFAULT_GROUP_ID])
    parser.add_argument('-a', dest='aid', type=str, nargs=1, default=[None])
    parser.add_argument('-e', dest='ext', type=str, nargs=1, default=[None])
    parser.add_argument('-c', dest='count', type=int, nargs=1, default=[1])
    parser.set_defaults(boolean=False)
    if s:
        args = parser.parse_args(shlex.split(s))
    else:
        args = parser.parse_args()
    verbose = args.verbose
    snapshots = args.snapshots
    gid = args.gid[0]
    aid = args.aid[0]
    ext = args.ext[0]
    count = args.count[0]
    repo = 'snapshots' if snapshots else 'releases'
    return nexus_ver(aid=aid, gid=gid, repo=repo, count=count, ext=ext, verbose=verbose)


def nexus_ver(aid, gid=DEFAULT_GROUP_ID, repo='releases', count=1, ext='', verbose=False):
    """Get artifact version info from Maven repo (Nexus).

    Args:
        aid: artifact id
        gid: group id
        repo: 'releases' or 'snapshots'
        count: number of latest versions to retrieve
        verbose: get more info on the retrieved versions
    Returns:
        Versions object.
    """
    mdata = metadata(artifact_id=aid, group_id=gid, repo=repo)
    versions = Versions(repo=repo, group_id=gid, artifact_id=aid)
    if not verbose:
        for v in mdata.latest_n_versions(n=count):
            versions.add(Version(version=v))
    else:
        if not ext:
            ext = find_ext(repo=repo, gid=gid, aid=aid, ver=mdata.latest_version())
        for ver in mdata.latest_n_versions(n=count):
            filename = '{aid}-{ver}.{ext}'.format(**locals())
            gid = gid.replace('.', '/')
            if repo == 'snapshots':
                response = requests.get(
                    NEXUS_URL + '/content/repositories/snapshots/{gid}/{aid}/{ver}/'.format(
                        **locals()))
                if response.ok:
                    line = [l for l in response.text.splitlines() if ext + '"' in l][-1]
                    line = line[0:line.rfind('<')]  # remove trailing </a> tag.
                    line = line[line.find('>') + 1:]  # remove leading <a> tag.
                    filename = line

            response = requests.get(
                NEXUS_URL + '/service/local/repositories/{repo}/content/{gid}/{aid}/{ver}/{filename}?describe=info&isLocal=true'.format(
                    **locals()))
            uploaded_date = 'unknown'
            if response.ok:
                uploaded = 0  # time
                uploaded = int(_findall(response.text, './data/uploaded')[0][0:10])
                uploaded_date = datetime.datetime.fromtimestamp(uploaded).strftime('%Y-%m-%d %H:%M:%S')
                versions.add(Version(version=ver, uploaded=uploaded_date))
    return versions


def find_ext(repo, gid, aid, ver):
    """Find extension of artifact."""
    ext_to_try = ['war', 'jar', 'swc', 'pom']
    for e in ext_to_try:
        response = requests.get(
            NEXUS_URL + '/service/local/artifact/maven/resolve?r={repo}&g={gid}&a={aid}&v={ver}&p={e}'.format(
                **locals()))
        if response.ok:
            return e
    return None


def latest_version(artifact_id, group_id=DEFAULT_GROUP_ID, repo='releases'):
    """Get the LATEST version of an artifact in Nexus with the given info.

    This function will attempt to find the version of an artifact in Nexus.
    Commonly, artifacts are found in the 'flex' subgroup.  So if the
    supplied group_id fails, this function then checks {group_id}/flex.
    If the artifact is found there, in the flex subgroup, the returned
    group_id is the subgroup with '/flex' appended to it.

    Args:
        group_id: defaults to DEFAULT_GROUP_ID.
        repo: 'releases' or 'snapshots', defaults to releases.
    Returns:
        The latest version as a string.
    """
    mdata = metadata(artifact_id=artifact_id, group_id=group_id, repo=repo)
    return mdata.latest_version()


def metadata(artifact_id, group_id=DEFAULT_GROUP_ID, repo='releases'):
    """Get ALL versions of an artifact in Nexus with the given info.

    This function will attempt to find the versions of an artifact in Nexus.
    Commonly, artifacts are found in the 'flex' subgroup.  So if the
    supplied group_id fails, this function then checks {group_id}/flex.
    If the artifact is found there, in the flex subgroup, the returned
    group_id is the subgroup with '/flex' appended to it.

    Args:
        group_id: defaults to DEFAULT_GROUP_ID.
        repo: 'releases' or 'snapshots', defaults to releases.
    Returns:
        A MavenMetadata object that contains all the versions.
    """
    group_id = group_id.replace('.', '/')
    response = requests.get(
        NEXUS_URL + '/service/local/repositories/{repo}/content/{group_id}/{artifact_id}/maven-metadata.xml'.format(
            **locals()))
    if response.status_code == 404:
        response = requests.get(
            NEXUS_URL + '/service/local/repositories/{repo}/content/{group_id}/flex/{artifact_id}/maven-metadata.xml'.format(
                **locals()))
        if response.status_code == 404:
            raise FileNotFoundError
        else:
            group_id = "${group_id}/flex"
    versions = _findall(response.text, './versioning/versions/version')
    return MavenMetadata(group_id=group_id, artifact_id=artifact_id, repo=repo, versions=versions)


def download(artifact_id, version, group_id=None, repo=None, ext=None, classifier=None):
    """Download an artifact from Nexus, but keep the file in memory.

    Args:
        group_id: defaults to DEFAULT_GROUP_ID.
        repo: 'releases' or 'snapshots', defaults to releases.
    Returns:
        Result object from HTTP get request.
    """
    if not group_id:
        group_id = DEFAULT_GROUP_ID
    if not repo:
        repo = 'releases'
    if not ext:
        [ext, classifier] = info(group_id, artifact_id, version)
    if 'SNAPSHOT' in version:
        repo = 'snapshots'
    try:
        url = NEXUS_URL + '/service/local/artifact/maven/content?r={repo}&g={group_id}&a={artifact_id}&v={version}&p={ext}'.format(
            **locals())
        if classifier:
            url += '&c={classifier}'.format(**locals())
        return requests.get(url)
    except urllib.error.HTTPError as e:
        return None


def getmd5(artifact_id, version, group_id=None, repo=None, ext=None):
    """Get the MD5 hash of an artifact in nexus.

    Args:
        artifact_id: required.
        version: required.
        group_id: optional.
        repo: either 'releases' or 'snapshots', optional.
        ext: The file extension of the artifact, optional.
    Returns:
        The MD5 hash value of the artifact, or None if the hash isn't found.
    """
    if not ext:
        ext = 'war'
    response = download(artifact_id=artifact_id,
                        version=version,
                        group_id=group_id,
                        repo=repo,
                        ext=ext + '.md5')
    if response.ok:
        return response.content.decode('utf8')
    return None


def save(artifact_id, version, group_id=None, repo=None, ext=None, classifier=None):
    """Saves an artifact from Nexus to the current working directory

    Args:
        group_id: defaults to DEFAULT_GROUP_ID.
        repo: 'releases' or 'snapshots', defaults to releases.
    Returns:
        The filename of the downloaded file, or None if the download failed
        (e.g. HTTP 404 error).
    """
    if not group_id:
        group_id = DEFAULT_GROUP_ID
    if not repo:
        repo = 'releases'
    if not ext:
        [ext, classifier] = info(group_id, artifact_id, version)
        if not ext:
            ext = 'war'  # default
            classifier = None  # default
    if 'SNAPSHOT' in version:
        repo = 'snapshots'
    try:
        url = NEXUS_URL + '/service/local/artifact/maven/content?r={repo}&g={group_id}&a={artifact_id}&v={version}&p={ext}'.format(
            **locals())
        if classifier:
            url += '&c={classifier}'.format(**locals())
        return wget.download(url), ext
    except urllib.error.HTTPError as e:
        return None, None


def quick_search(criteria):
    """Searches Nexus and returns XML results."""
    url = NEXUS_URL + '/service/local/lucene/search?q={criteria}'.format(**locals())
    response = requests.get(url)
    return response.text


def info(group_id, artifact_id, version):
    """Determine the extension and classifier of an artifact in Nexus.

    Returns:
        A tuple of (extension, classifier).
    """
    xml = quick_search(artifact_id)
    root = ET.fromstring(xml)
    infos = []
    for artifact in root.iter('artifact'):
        g = artifact.find('groupId').text
        a = artifact.find('artifactId').text
        v = artifact.find('version').text
        if [g, a, v] == [group_id, artifact_id, version]:
            for link in artifact.findall('artifactHits/artifactHit/artifactLinks/artifactLink'):
                ext = link.find('extension').text
                classifier = None
                if link.find('classifier') is not None:
                    classifier = link.find('classifier').text
                infos.append(ArtifactInfo(ext, classifier))
    # TODO: use new approach of taking the artifact that has the largest file size?  Might require an extra call to Nexus for each classifier for each artifact.
    # TODO: support rpms here, also need a way to list contents of rpm.
    ignored_classifiers = ['classes', 'sources', 'javadoc', 'libs', 'tests']
    infos = [i for i in infos if i.classifier not in ignored_classifiers]
    for i in infos:
        if i.ext == 'zip' and i.classifier == 'full':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'zip' and i.classifier == 'uber':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'zip' and i.classifier == 'JAVA':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'tar.gz' and i.classifier == 'bundle':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'tar.gz' and i.classifier == 'job':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'war':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'jar':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'tar.gz':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'tar':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'zip':
            return i.ext, i.classifier
    for i in infos:
        if i.ext == 'pom':
            return i.ext, i.classifier
    else:
        return None, None


def find_possible_groupIds_artifactIds(search_criteria):
    """Searches Nexus for possible groupId/artifactId combos.

    Returns:
        A map of artifactId -> groupId.  Each groupId in the
        results will start with DEFAULT_GROUP_ID.
    """
    xml = quick_search(search_criteria)
    root = ET.fromstring(xml)
    matches = {}
    for a in root.iter('artifact'):
        gid = a.find('groupId').text
        aid = a.find('artifactId').text
        if DEFAULT_GROUP_ID in gid and aid not in matches:
            matches[aid] = gid
    return matches


def _findall(xml, tag):
    """Parses XML and finds all values of the given tag.

    Args:
        tag: The full path of the tag we're looking for, e.g. './data/artifact'.
    Returns:
        A list of values.
    """
    root = ET.fromstring(xml)
    elements = root.findall(tag)
    return [e.text for e in elements]
