import shutil

import pytest
from acclimatise import explore_command


@pytest.mark.skipif(not shutil.which("bwa"), reason="bwa is not installed")
def test_explore_bwa():
    command, cache = explore_command(["bwa"])
    assert len(command.subcommands) == 14
    assert len(command.positional) == 0

    # Check cache
    assert len(cache) > 15
    # Cache should have no duplicates
    all_commands = [
        tuple(cache_entry.command + cache_entry.generated_from)
        for cache_entry in cache.values()
    ]
    assert len(set(all_commands)) == len(all_commands)

    # Check that we parsed bwa mem correctly
    mem = command.subcommands[1]
    assert len(mem.positional) == 3
    assert len(mem.subcommands) == 0
    assert len(mem.named) >= 30


@pytest.mark.skipif(
    not shutil.which("podchecker"), reason="podchecker is not installed"
)
def test_explore_podchecker():
    command, cache = explore_command(["podchecker"])
    assert len(command.subcommands) == 0
    assert len(command.positional) == 1
    assert len(command.named) == 2
