import os
import shutil
import tempfile

import pytest

from acclimatise import explore_command

from .util import (
    HelpText,
    all_ids,
    all_tests,
    convert_validate,
    ensure_conda,
    skip_not_installed,
)


@pytest.mark.parametrize("test", all_tests, ids=all_ids)
def test_explore(test: HelpText):
    """
    A comprehensive end-to-end test that tests the parser and converters, after exploring a given command
    """
    if not shutil.which(test.cmd[0]):
        pytest.skip("{} is not installed".format(test.cmd[0]))

    try:
        ensure_conda()
    except:
        pytest.skip("Not in a conda environment")

    # For speed's sake, only explore to depth 2
    command = explore_command(test.cmd, max_depth=1)

    # Check we parsed correctly
    assert len(command.subcommands) == test.subcommands
    assert len(command.positional) == test.positional
    assert len(command.named) == test.named

    # Check this can be converted properly to all formats
    convert_validate(command, explore=True)


@skip_not_installed("dinosaur")
@pytest.mark.timeout(360)
def test_explore_dinosaur():
    """
    Python has an issue with killing process trees, whereby the subprocess runs another subprocess.
    This tests that dinosaur
    :return:
    """
    command = explore_command(["dinosaur"], max_depth=1)


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_explore_bwa():
    """
    This tests specifically that exploring bwa yields a proper bwa mem
    """
    command = explore_command(["bwa"], max_depth=1)

    # Check that we parsed bwa mem correctly
    mem = command.subcommands[1]
    assert len(mem.positional) == 3
    assert len(mem.subcommands) == 0
    assert len(mem.named) >= 30
