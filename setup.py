#!/usr/bin/env python3
from setuptools import find_packages, setup

setup(
    packages=find_packages(exclude="test"),
    install_requires=[
        "pyparsing",
        "jinja2",
        "spacy",
        "cwlgen",
        "dataclasses",
        "miniwdl",
        "wordsegment",
        "inflection",
        "illusional.wdlgen~=0.2",
        "ruamel.yaml>=0.16.5",
    ],
    entry_points={"console_scripts": ["acclimatise = acclimatise.cli:main"]},
    extras_require={"dev": ["pytest", "pre-commit"],},
)
