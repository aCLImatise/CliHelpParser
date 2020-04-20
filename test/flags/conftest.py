import pytest
from acclimatise.flag_parser.parser import CliParser


@pytest.fixture(scope="function")
def parser():
    return CliParser()
