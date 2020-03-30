import shutil

import pytest
from acclimatise.converter.wdl import WdlGenerator
from acclimatise.flag_parser.parser import CliParser
from acclimatise.parser import execute_cmd
from WDL import parse_document


@pytest.mark.skipif(
    not shutil.which("htseq-count"), reason="htseq-count is not installed"
)
def test_htseq():
    help_text = execute_cmd(["htseq-count", "--help"])
    cmd = CliParser().parse_command(help_text, ["htseq-count"])
    wdl = WdlGenerator().generate_wrapper(cmd)

    # Check that the generated WDL parses
    parse_document(wdl)
