#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build and installation routines for task-wizard.

"""

from setuptools import setup, find_packages


setup(
    name="turingarena",
    version="0.2",
    author="",
    author_email="",
    url="",
    download_url="",
    description="",
    entry_points={
        "console_scripts": [
            "turingarena=turingarena.cli.main:main",
        ],
    },
    namespace_packages=["turingarena_protocols"],
    packages=find_packages(),
    package_data={
        'turingarena': ['**/templates/**', '**/*static/**'],
    },
    keywords="",
    license="",
    classifiers=[],
    install_requires=[
        "docopt",
        "tatsu",
        "jinja2",
        "pyyaml",
        "coloredlogs",
        "WerkZeug",
        "requests",
        "requests-unixsocket",
    ],
)
