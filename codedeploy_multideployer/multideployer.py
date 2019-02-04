#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

from . import __version__
import yaml
import argparse
import textwrap
import logging
import sys
import os
import uuid
import urllib.parse
import urllib.request
import tarfile
import shutil
import sh

MULTIDEPLOYER_DIR = '/var/lib/codedeploy-multideployer'
MAX_REVISIONS = 5

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)


class ConfigFormatError(Exception):
    """Yaml file not in correct format"""
    pass


def check_yaml_config(yaml_config, options):
    try:
        assert yaml_config['version'] == 1.0
    except AssertionError:
        raise ConfigFormatError('Version not 1.0')
    try:
        assert type(yaml_config['apps']) is list
    except:
        raise ConfigFormatError('"apps" does not exist or is not a list.')
    for app in yaml_config['apps']:
        try:
            assert type(app) is dict
        except AssertionError:
            raise ConfigFormatError('App ' + app +
                                    ' definition is not a dict.')
        try:
            assert app['name']
            assert app['release']
            assert app['source']
        except KeyError:
            raise ConfigFormatError('App does not have all required fields: ' +
                                    'name, release, source.')


def download_bundle(app_name, app_source, app_release, github_token,
                    deploy_dir):
    log.debug("Cloning repository: " + app_name + " " + app_source + ":" +
              app_release)
    o = urllib.parse.urlparse(app_source)
    if o.scheme == 'github':
        url = "https://api.github.com/repos/" + o.netloc + o.path + \
              "/tarball/" + app_release
        if github_token:
            final_url = url + "?access_token=" + github_token
        else:
            final_url = url
        destdir = deploy_dir + "/" + app_name
        os.makedirs(destdir)
        log.info("Downloading bundle: " + url + " to " + destdir)
        urllib.request.urlretrieve(final_url, destdir + "/bundle.tar.gz")
        bundle_file = tarfile.open(destdir + "/bundle.tar.gz", mode="r:gz")
        log.debug("Extracting bundle to " + destdir + "/bundle")
        os.makedirs(destdir + "/bundle")
        for member in bundle_file.getmembers():
            if member.isreg():
                member.name = "/".join(member.name.split("/")[1:])
                bundle_file.extract(member, destdir + "/bundle")
    else:
        raise Exception('Source ' + o.scheme + ' not supported.')


def deploy(app_name, release, deploy_dir, codedeploy_local_path):
    log.info("Deploying app: " + app_name)
    if not os.path.isfile(deploy_dir + "/" + app_name + "/bundle/appspec.yml"):
        raise Exception("appspec.yml not found in app " + app_name)
    if not os.path.isfile(codedeploy_local_path):
        raise Exception("codedeploy-local not found in " +
                        codedeploy_local_path)
    codedeploy_local = sh.Command(codedeploy_local_path,
                                  _env={"GIT_COMMIT": release})
    output = codedeploy_local("--bundle-location", deploy_dir + "/" +
                              app_name + "/bundle",
                              "--type", "directory",
                              "--deployment-group", app_name +
                              "-local-deployment-application")
    log.info(output)
    # XXX codedeploy-local always return 0 (even if a script failed)
    if "Your local deployment failed while trying to execute your script" \
            in output:
        raise Exception("codedeploy-local failed running some script")


def multideploy(options):
    """Deploy apps specified in config file"""
    # Check if user == root
    if os.getuid() != 0:
        raise OSError("You need to have root privileges to run this script.")

    # Read config from yaml
    with open(options.config, 'r') as stream:
        try:
            yaml_config = yaml.load(stream)
        except yaml.YAMLError as e:
            raise ConfigFormatError(format(e))

    # Check if yaml is valid
    check_yaml_config(yaml_config, options)

    # Generate unique uuid for this deploy
    deploy_id = str(uuid.uuid4())
    log.debug("Deploy id: " + deploy_id)
    deploy_dir = MULTIDEPLOYER_DIR + "/deploys/" + deploy_id

    # Select deploying apps
    if not options.apps:
        deploy_apps = yaml_config['apps']
    else:
        deploy_apps = []
        for app in options.apps:
            for config_app in yaml_config['apps']:
                if config_app['name'] == app:
                    deploy_apps.append(config_app)
    log.debug("Deploying to: " + str(deploy_apps))

    # Create required directories don't exist
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)

    # try to load last deploy status
    try:
        with open(MULTIDEPLOYER_DIR + '/last_state.yaml', 'r') as stream:
            try:
                last_state = yaml.load(stream)
            except yaml.YAMLError as e:
                raise Exception(format(e))
    except OSError as e:
        last_state = {}
    log.debug("Last state: " + str(last_state))

    state = {}
    for app in deploy_apps:
        if app.get('force', False) or app['release'] != \
                last_state.get(app['name'], {}).get('release'):
            download_bundle(app['name'], app['source'], app['release'],
                            options.github_token, deploy_dir)
            deploy(app['name'], app['release'], deploy_dir,
                   options.codedeploy_local_path)
        else:
            log.debug(app['name'] + ' already deployed with release ' +
                      app['release'] + ". Skipping...")
        state[app['name']] = {'release': app['release']}

    # Write to last_state.yaml
    with open(MULTIDEPLOYER_DIR + '/last_state.yaml', 'w') as outfile:
        yaml.dump(state, outfile, default_flow_style=False)
    # Clean old deploy directories
    search_dir = MULTIDEPLOYER_DIR + "/deploys/"
    os.chdir(search_dir)
    dirs = filter(os.path.isdir, os.listdir(search_dir))
    dirs = [os.path.join(search_dir, d) for d in dirs]
    dirs.sort(key=os.path.getmtime)
    for d in dirs[:-MAX_REVISIONS]:
        log.debug("Removing old revision directory " + d)
        shutil.rmtree(d)


def start():
    """
    Deploys multiple CodeDeploy projects in one shot.

    environment variables:
      MULTIDEPLOYER_GITHUB_TOKEN: Same as --github-token
      MULTIDEPLOYER_CODEDEPLOY_LOCAL_PATH: Same as --codedeploy-local-path
    """
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(start.__doc__),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)
    parser.add_argument('-d', '--debug',
                        help="Print debug info",
                        action="store_const",
                        dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument('-v', '--verbose',
                        help="Be more verbose",
                        action="store_const",
                        dest="loglevel", const=logging.INFO)
    parser.add_argument('-f', '--force',
                        help="Force deploys even if it already has the " +
                             "same version",
                        action="store_true",
                        default=False)
    parser.add_argument('-a', '--app',
                        help="Only deploy to this app. Can be called " +
                             "multiple times",
                        dest="apps",
                        metavar="APP_NAME",
                        action="append")
    parser.add_argument('-g', '--github-token',
                        help="GitHub OAauth token to be used to download " +
                             "private repositories",
                        default=os.environ.get('MULTIDEPLOYER_GITHUB_TOKEN',
                                               None))
    parser.add_argument('-c', '--codedeploy-local-path',
                        help="Full path to the codedeploy-local script",
                        default=os.environ.get(
                            'MULTIDEPLOYER_CODEDEPLOY_LOCAL_PATH',
                            '/opt/codedeploy-agent/bin/codedeploy-local'))
    parser.add_argument('--config',
                        default='multideployer.yaml',
                        metavar="CONFIG_FILE",
                        help="Config file. Default: multideployer.yaml")
    parser.add_argument('-l', '--log',
                        default='/var/log/codedeploy-multideployer/' +
                                'multideployer.log',
                        metavar="LOG_FILE",
                        help="Log file")

    options = parser.parse_args()
    try:
        if not os.path.exists(os.path.dirname(options.log)):
            os.makedirs(os.path.dirname(options.log))
        log.addHandler(logging.FileHandler(options.log))
        log.addHandler(logging.StreamHandler(sys.stdout))
        logging.basicConfig(level=options.loglevel)
        log.debug('Options: ' + str(options))

        multideploy(options)
    except OSError as e:
        log.error(format(e))
        sys.exit(1)
    except ConfigFormatError as e:
        log.error('File ' + options.config + ' not in expected format: ' +
                  format(e))
        sys.exit(1)
    except Exception as e:
        log.error(format(e))
        sys.exit(1)


if __name__ == '__main__':
    start()
