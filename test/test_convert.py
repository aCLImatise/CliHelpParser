import itertools
import tempfile
from io import StringIO
from pathlib import Path

from aclimatise import explore_command
from aclimatise.converter.yml import YmlGenerator
from aclimatise.yaml import yaml

from .util import convert_validate, skip_not_installed

# Note: the parse and explore tests run conversion tests already. These tests are for specific edge cases


def test_concise_dump(samtools_cmd):
    """
    Test that a round trip dump results in no subcommands
    """
    assert len(samtools_cmd.subcommands) > 0
    gen = YmlGenerator(dump_associations=False)
    io = StringIO()
    serial = gen.save_to_string(samtools_cmd)
    io.write(serial)
    io.seek(0)
    parsed = yaml.load(io)
    assert len(parsed.subcommands) == 0


def test_verbose_dump(samtools_cmd):
    """
    Test that a round trip dump results in retaining subcommands
    """
    assert len(samtools_cmd.subcommands) > 0
    gen = YmlGenerator(dump_associations=True)
    io = StringIO()
    serial = gen.save_to_string(samtools_cmd)
    io.write(serial)
    io.seek(0)
    parsed = yaml.load(io)
    assert len(parsed.subcommands) > 0


def test_premade_samtools(samtools_cmd):
    """
    Use a command tree that was generated beforehand, to quickly detect issues relating to the conversion of command
    trees
    """
    convert_validate(samtools_cmd, explore=True)


def test_premade_bedtools(bedtools_cmd):
    """
    Use a command tree that was generated beforehand, to quickly detect issues relating to the conversion of command
    trees
    """
    convert_validate(bedtools_cmd, explore=True)


@skip_not_installed("samtools")
@skip_not_installed("samtools.pl")
def test_explore_samtools_pl(yaml_converter):
    """
    Tests that commands with a non-standard file extension include their extension in the final output, and don't
    override another command with the same stem
    """
    samtools = explore_command(["samtools"], max_depth=0)
    samtools_pl = explore_command(["samtools.pl"], max_depth=0)
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir)
        filenames = set()
        for path, command in itertools.chain(
            yaml_converter.generate_tree(samtools, temp_dir),
            yaml_converter.generate_tree(samtools_pl, temp_dir),
        ):
            filenames.add(path.name)

        assert filenames == {"samtools.yml", "samtools.pl.yml"}
