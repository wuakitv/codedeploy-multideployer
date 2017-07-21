#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

from . import __version__
import yaml
import argparse
import logging
import sys

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)


class ConfigFormatError(Exception):
    """Yaml file not in correct format"""
    pass


def deploy(options):
    """Deploy apps specified in config file"""
    # Read config from yaml
    with open(options.config, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as e:
            raise ConfigFormatError(format(e))

    # Check if yaml is valid
    try:
        assert config['version'] == 1.0
    except AssertionError:
        raise ConfigFormatError('Version not 1.0')
    try:
        assert type(config['apps']) is list
    except:
        raise ConfigFormatError('"apps" does not exist or is not a list.')
    for app in config['apps']:
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

        print(app)


def start():
    """Main function"""

    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)
    parser.add_argument('-d', '--debug',
                        help="Print debug info.",
                        action="store_const",
                        dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument('-v', '--verbose',
                        help="Be more verbose.",
                        action="store_const",
                        dest="loglevel", const=logging.INFO)
    parser.add_argument('--config',
                        default='multideployer.yaml',
                        help="Config file. Default: multideployer.yaml")

    options = parser.parse_args()
    logging.basicConfig(level=options.loglevel)
    log.debug('Options: ' + str(options))
    try:
        deploy(options)
    except FileNotFoundError:
        log.error('File ' + options.config + ' not found.')
        sys.exit(1)
    except ConfigFormatError as e:
        log.error('File ' + options.config + ' not in expected format: ' +
                  format(e))
        sys.exit(1)


if __name__ == '__main__':
    start()
