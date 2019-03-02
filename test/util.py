import subprocess
from declivity.parser import CliParser
import pytest

def get_help(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    return (proc.stdout or proc.stderr).decode('utf_8')

@pytest.fixture
def parser():
    return CliParser()

