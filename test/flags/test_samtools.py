import shutil

import pytest

from acclimatise.execution import execute_cmd


def test_samtools(parser, samtools_help):
    # Parse the root samtools command
    samtools = parser.parse_command(name=["samtools"], cmd=samtools_help)
    assert len(samtools.named) == 0
    assert len(samtools.positional) > 25


@pytest.mark.skipif(not shutil.which("samtools"), reason="samtools is not installed")
def test_samtools_index(parser):
    # Parse help
    help_text = execute_cmd(["samtools", "index"])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 1
    # There are two positional arguments
    assert len(flag_sections[0]) == 4
