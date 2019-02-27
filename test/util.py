import subprocess
from declivity import parser2
import pytest

def get_help(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    return (proc.stdout or proc.stderr).decode('utf_8')

@pytest.fixture
def parser():
    return parser2.CliParser()

