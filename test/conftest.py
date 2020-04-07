from pkg_resources import resource_filename

import pytest
from acclimatise.flag_parser.parser import CliParser


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
def bedtools_help():
    with open(resource_filename(__name__, "test_data/bedtools.txt")) as fp:
        return fp.read()


@pytest.fixture
def bedtools_coverage_help():
    with open(resource_filename(__name__, "test_data/bedtools_coverage.txt")) as fp:
        return fp.read()
