from declivity.parser import CliParser
from declivity.converter.wdl import WdlGenerator
from test.util import get_help

from WDL import parse_document
import shutil
import pytest


@pytest.mark.skipif(not shutil.which('htseq-count'), reason='htseq-count is not installed')
def test_htseq():
    help_text = get_help(['htseq-count', '--help'])
    cmd = CliParser().parse_command(help_text, ['htseq-count'])
    wdl = WdlGenerator().generate_wrapper(cmd)

    # Check that the generated WDL parses
    parse_document(wdl)
