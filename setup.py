#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

from distutils.core import setup
from setuptools import find_packages
import codedeploy_multideployer
import re


def parse_requirements(file_name):
    requirements = []

    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements


reqs = parse_requirements('requirements.txt')

setup(
    name='codedeploy-multideployer',
    version=codedeploy_multideployer.__version__,
    description="Deploy multiple applications in one deployment group.",
    author="Rakuten TV Systems department",
    author_email="systems@wuaki.tv",
    packages=find_packages(),
    install_requires=reqs,
    scripts=["multideployer"],
)
