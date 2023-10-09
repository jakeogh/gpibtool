# -*- coding: utf-8 -*-

import sys

from setuptools import find_packages
from setuptools import setup

if not sys.version_info[0] == 3:
    sys.exit("Python 3 is required. Use: 'python3 setup.py install'")

dependencies = [
    "icecream @ git+https://git@github.com/jakeogh/icecream",
    "click",
    "PyVISA-py",
    "sh",
    "gpib-ctypes",
    "asserttool @ git+https://git@github.com/jakeogh/asserttool",
    "bnftool @ git+https://git@github.com/jakeogh/bnftool",
    "stdiotool @ git+https://git@github.com/jakeogh/stdiotool",
    "mp8 @ git+https://git@github.com/jakeogh/mp8",
    "unmp @ git+https://git@github.com/jakeogh/unmp",
]

config = {
    "version": "0.1",
    "name": "gpibtool",
    "url": "https://github.com/jakeogh/gpibtool",
    "license": "ISC",
    "author": "Justin Keogh",
    "author_email": "github.com@v6y.net",
    "description": "Common functions for GPIB control",
    "long_description": __doc__,
    "packages": find_packages(exclude=["tests"]),
    "package_data": {"gpibtool": ["py.typed"]},
    "include_package_data": True,
    "zip_safe": False,
    "platforms": "any",
    "install_requires": dependencies,
    "entry_points": {
        "console_scripts": [
            "gpibtool=gpibtool.gpibtool:cli",
        ],
    },
}

setup(**config)
