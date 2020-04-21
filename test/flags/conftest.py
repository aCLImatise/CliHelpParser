import pytest
from acclimatise.flag_parser.parser import CliParser


@pytest.fixture
def parser():
    return CliParser()
