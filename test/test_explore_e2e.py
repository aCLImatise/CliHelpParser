import shutil
import tempfile

import pytest

from acclimatise import execute_cmd, explore_command

from .util import HelpText, all_ids, all_tests, convert_validate


@pytest.mark.parametrize("test", all_tests, ids=all_ids)
def test_explore(test: HelpText):
    """
    A comprehensive end-to-end test that tests the parser and converters, after exploring a given command
    """
    if not shutil.which(test.cmd[0]):
        pytest.skip("{} is not installed".format(test.cmd[0]))

    # For speed's sake, only explore to depth 2
    command = explore_command(test.cmd, max_depth=2)

    # Check we parsed correctly
    assert len(command.subcommands) == test.subcommands
    assert len(command.positional) == test.positional
    assert len(command.named) == test.named

    # Check this can be converted properly to all formats
    convert_validate(command, explore=True)


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_explore_bwa():
    """
    This tests specifically that exploring bwa yields a proper bwa mem
    """
    command = explore_command(["bwa"])

    # Check that we parsed bwa mem correctly
    mem = command.subcommands[1]
    assert len(mem.positional) == 3
    assert len(mem.subcommands) == 0
    assert len(mem.named) >= 30


def test_samtools_sort():
    execute_cmd(["samtools", "sort"])
