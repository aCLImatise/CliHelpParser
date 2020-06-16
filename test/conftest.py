from textwrap import dedent

import pytest
from pkg_resources import resource_filename

from acclimatise.flag_parser.parser import CliParser
from acclimatise.yaml import yaml


@pytest.fixture()
def bedtools_cmd():
    with open(resource_filename(__name__, "test_data/bedtools/bedtools.yml")) as fp:
        return yaml.load(fp)


@pytest.fixture()
def samtools_cmd():
    with open(resource_filename(__name__, "test_data/samtools/samtools.yml")) as fp:
        return yaml.load(fp)


@pytest.fixture
def samtools_help():
    with open(resource_filename(__name__, "test_data/samtools.txt")) as fp:
        return fp.read()


@pytest.fixture
def htseq_help():
    with open(resource_filename(__name__, "test_data/htseq_count.txt")) as fp:
        return fp.read()


@pytest.fixture
def bwamem_help():
    with open(resource_filename(__name__, "test_data/bwa_mem.txt")) as fp:
        return fp.read()


@pytest.fixture
def pisces_help():
    with open(resource_filename(__name__, "test_data/pisces.txt")) as fp:
        return fp.read()


@pytest.fixture
def bwa_help():
    with open(resource_filename(__name__, "test_data/bwa.txt")) as fp:
        return fp.read()


@pytest.fixture
def bwa_bwt2sa_help():
    with open(resource_filename(__name__, "test_data/bwa_bwt2sa.txt")) as fp:
        return fp.read()


@pytest.fixture
def bedtools_help():
    with open(resource_filename(__name__, "test_data/bedtools.txt")) as fp:
        return fp.read()


@pytest.fixture
def bedtools_coverage_help():
    with open(resource_filename(__name__, "test_data/bedtools_coverage.txt")) as fp:
        return fp.read()


@pytest.fixture
def podchecker_help():
    with open(resource_filename(__name__, "test_data/podchecker.txt")) as fp:
        return fp.read()


@pytest.fixture()
def process():
    def process_help_section(help):
        """
        Does some preprocessing on a help text segment to facilitate testing
        """
        help = help.strip("\n")
        return dedent(help)

    return process_help_section
