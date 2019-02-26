#!/usr/bin/env python3
from setuptools import setup

setup(
    name='declivity',
    packages=['declivity'],
    version='0.0.1',
    install_requires=[
        'parsimonious'
    ],
    entry_points={
        'console_scripts': [
        ]
    },
    extras_require={
        'dev': [
            'pytest'
        ],
    }
)
