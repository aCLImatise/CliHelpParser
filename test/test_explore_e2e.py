import os
import shutil
import tempfile
from unittest.mock import Mock, patch

import pytest

from aclimatise import explore_command
from aclimatise.model import Command, Positional

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
    test.run_assertions(command, explore=True)


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
    mem = [cmd for cmd in command.subcommands if cmd.command[1] == "mem"][0]
    assert len(mem.positional) == 3
    assert len(mem.subcommands) == 0
    assert len(mem.named) >= 30


def test_repeat_positionals():
    """
    Test that, if we have multiple duplicate positionals, only the first is tested
    """
    parent = Command(
        command=[],
        positional=[
            Positional(name="a", description="", position=i) for i in range(10)
        ],
    )
    child = Command(command=[])

    count = 0

    def mock_convert(*args, **kwargs):
        nonlocal count
        if count == 0:
            count += 1
            return parent
        return child

    # with patch("aclimatise.execution.help.CliHelpExecutor.explore", new=lambda *args, **kwargs: child):
    with patch(
        "aclimatise.execution.help.CliHelpExecutor.convert",
        new=Mock(side_effect=mock_convert),
    ) as mocked:
        explore_command([])

        # We should only call convert twice, once for the parent and once for the child, since there's only one unique positional
        assert mocked.call_count == 2
