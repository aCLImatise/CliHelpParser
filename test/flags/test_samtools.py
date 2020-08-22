import shutil

import pytest

from acclimatise.model import Flag


def test_samtools_bedcov_j(parser):
    text = """
      -j                  do not include deletions (D) and ref skips (N) in bedcov computation
    """
    flag = parser.flag.parseString(text)[0]
    assert isinstance(flag, Flag)
    assert flag.synonyms[0] == "-j"


def test_samtools_bedcov_qjfmt(parser):
    text = """
      -Q <int>            mapping quality threshold [0]
      -j                  do not include deletions (D) and ref skips (N) in bedcov computation
      --input-fmt-option OPT[=VAL]
               Specify a single input file format option in the form
               of OPTION or OPTION=VALUE
    """
    flags = list(parser.flags.setDebug().searchString(text)[0])
    assert len(flags) == 3


def test_samtools(parser, samtools_help):
    # Parse the root samtools command
    samtools = parser.parse_command(name=["samtools"], cmd=samtools_help)
    assert len(samtools.named) == 0
    assert len(samtools.positional) > 25


@pytest.mark.skipif(not shutil.which("samtools"), reason="samtools is not installed")
def test_samtools_index(parser, local_executor):
    # Parse help
    help_text = local_executor.execute(["samtools", "index"])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 1
    # There are two positional arguments
    assert len(flag_sections[0]) == 4
