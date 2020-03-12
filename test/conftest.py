from acclimatise.flag_parser.parser import CliParser
import pytest

@pytest.fixture
def parser():
    return CliParser()

