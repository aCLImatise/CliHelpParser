import shutil

import pytest

from aclimatise.flag_parser.parser import CliParser


def test_singularity_style_flags(parser):
    flag = parser.flag_block.parseString(
        "    -n|--name   Specify a custom container name (first priority)"
    )[0]
    assert len(flag.synonyms) == 2
    assert flag.synonyms == ["-n", "--name"]


@pytest.mark.skipif(
    not shutil.which("singularity"), reason="singularity is not installed"
)
def test_singularity_pull(local_executor):
    parser = CliParser(parse_positionals=False)

    # Parse help
    help_text = local_executor.execute(["singularity", "pull", "--help"])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 1
    # There are two positional arguments
    assert len(flag_sections[0]) >= 5
