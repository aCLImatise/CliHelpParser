import itertools
import tempfile
from pathlib import Path

from acclimatise import explore_command

from .util import convert_validate, skip_not_installed


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
