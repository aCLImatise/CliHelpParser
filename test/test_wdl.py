from declivity.parser import CliParser
from declivity.converter.wdl import make_tasks
from test.util import get_help

from wdl_parser import version_1_0


def test_bwa():
    help_text = get_help(['bwa', 'mem'])
    cmd = CliParser().parse_command(help_text, ['bwa', 'mem'])
    wdl = make_tasks(cmd)

    # Check that the generated WDL parses
    version_1_0.parse(wdl)
