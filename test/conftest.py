from pkg_resources import resource_filename

import pytest
from acclimatise.flag_parser.parser import CliParser


@pytest.fixture
def htseq_help():
    with open(resource_filename(__name__, "htseq.txt")) as fp:
        return fp.read()


@pytest.fixture
def bwamem_help():
    with open(resource_filename(__name__, "bwamem.txt")) as fp:
        return fp.read()


@pytest.fixture
def pisces_help():
    with open(resource_filename(__name__, "pisces.txt")) as fp:
        return fp.read()
