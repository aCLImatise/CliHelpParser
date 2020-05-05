import shutil
import tempfile

from WDL import parse_document

import pytest
from acclimatise import explore_command
from acclimatise.converter.wdl import WdlGenerator
from acclimatise.flag_parser.parser import CliParser


@pytest.mark.skipif(
    not shutil.which("htseq-count"), reason="htseq-count is not installed"
)
def test_htseq():
    cmd = explore_command(["htseq-count"])

    with tempfile.TemporaryDirectory() as tmpdir:
        wrappers = list(WdlGenerator().generate_tree(cmd, tmpdir))

        # htseq-count has no subcommands
        assert len(wrappers) == 1

        for wrapper in wrappers:
            content = wrapper.read_text()

            # Check that the generated WDL parses
            parse_document(content)


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_bwa():
    cmd = explore_command(["bwa"])

    with tempfile.TemporaryDirectory() as tmpdir:
        wrappers = list(WdlGenerator().generate_tree(cmd, tmpdir))

        # bwa has many subcommands
        assert len(wrappers) > 10

        for wrapper in wrappers:
            content = wrapper.read_text()

            # Check that the generated WDL parses
            parse_document(content)
