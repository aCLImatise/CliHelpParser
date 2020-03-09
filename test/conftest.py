from declivity.parser import CliParser
import pytest

@pytest.fixture
def parser():
    return CliParser()

