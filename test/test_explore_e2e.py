import shutil
from itertools import product

import pytest

from acclimatise import explore_command

from .util import all_tests, convert_validate, validators


@pytest.mark.parametrize("test", all_tests)
def test_explore(test):
    """
    A comprehensive end-to-end test that tests the parser and converters, after exploring a given command
    """
    if not shutil.which(test.cmd[0]):
        pytest.skip("{} is not installed".format(test.cmd[0]))

    # Check we parsed correctly
    command = explore_command(test.cmd)
    assert len(command.subcommands) == test.subcommands
    assert len(command.positional) == test.positionals
    assert len(command.named) == test.named

    # Check this can be converted properly to all formats
    convert_validate(command)


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
