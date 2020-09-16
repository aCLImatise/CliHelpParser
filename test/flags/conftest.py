import pytest

from aclimatise.flag_parser.parser import CliParser


@pytest.fixture
def parser():
    return CliParser()
