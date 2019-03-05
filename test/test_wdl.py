from declivity.parser import CliParser
from declivity.converter.wdl import make_tasks
from test.util import get_help

def test_bwa():
    help_text = get_help(['bwa', 'mem'])
    cmd = CliParser().parse_command(help_text, ['bwa', 'mem'])
    wdl = make_tasks(cmd)
