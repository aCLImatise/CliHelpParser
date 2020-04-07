import shutil

import pytest
from acclimatise import execute_cmd
from acclimatise.flag_parser.parser import CliParser


@pytest.mark.skipif(not shutil.which("samtools"), reason="samtools is not installed")
def test_samtools_index(parser):
    # Parse help
    help_text = execute_cmd(["samtools", "index"])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 1
    # There are two positional arguments
    assert len(flag_sections[0]) == 4
