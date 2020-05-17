import shutil

import pytest

from acclimatise import explore_command


@pytest.mark.skipif(not shutil.which("false"), reason="false is not installed")
def test_explore_false():
    # This is basically a check that a program that itself crashes, won't crash aCLImatise
    command = explore_command(["false"])
    assert len(command.subcommands) == 0
    assert len(command.positional) == 0


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_explore_bwa():
    command = explore_command(["bwa"])
    assert len(command.subcommands) == 14
    assert len(command.positional) == 0

    # Check that we parsed bwa mem correctly
    mem = command.subcommands[1]
    assert len(mem.positional) == 3
    assert len(mem.subcommands) == 0
    assert len(mem.named) >= 30


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_explore_bwa_bwtupdate():
    command = explore_command(["bwa", "bwtupdate"])
    assert len(command.subcommands) == 0
    assert len(command.positional) == 1


@pytest.mark.skipif(
    not shutil.which("podchecker"), reason="podchecker is not installed"
)
def test_explore_podchecker():
    command = explore_command(["podchecker"])
    assert len(command.subcommands) == 0
    assert len(command.positional) == 1
    assert len(command.named) == 2
