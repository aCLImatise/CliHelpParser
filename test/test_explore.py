import shutil

import pytest
from acclimatise import explore_command


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_explore_bwa(bwa_help):
    command = explore_command(["bwa"])
    assert len(command.subcommands) == 14
    assert len(command.positional) == 0

    # Check that we parsed bwa mem correctly
    mem = command.subcommands[1]
    assert len(mem.positional) == 3
    assert len(mem.subcommands) == 0
    assert len(mem.named) >= 30