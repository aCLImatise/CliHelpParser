#!/usr/bin/env python3
from setuptools import setup

setup(
    name='declivity',
    packages=['declivity'],
    version='0.0.1',
    install_requires=[
        'pyparsing',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'declivity = declivity.cli:main'
        ]
    },
    extras_require={
        'dev': [
            'pytest'
        ],
    }
)
