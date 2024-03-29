#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from ocarina import version

requirements = [
    "requests",
    "colorama",
    "tabulate",
    "requests_oauthlib",
    "rich",
    "ffurf@git+https://github.com/SamStudio8/ffurf.git@42e95ecb63bc0d4b2be0813c5dc0beec1dc5e319",
]

test_requirements = [

]

setuptools.setup(
    name="ocarina",
    version=version.__version__,
    url="https://github.com/samstudio8/ocarina",

    description="",
    long_description="",

    author="Sam Nicholls",
    author_email="sam@samnicholls.net",

    maintainer="Sam Nicholls",
    maintainer_email="sam@samnicholls.net",

    packages=setuptools.find_packages(),
    install_requires=requirements,

    entry_points = {
        'console_scripts': [
            'ocarina = ocarina.client:cli',
        ]
    },

    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
    ],

    test_suite="tests",
    tests_require=test_requirements,

)
