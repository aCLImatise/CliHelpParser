import itertools
import tempfile
from pathlib import Path

import pytest
from WDL import parse_document

from aclimatise import explore_command
from aclimatise.converter.cwl import CwlGenerator
from aclimatise.converter.wdl import WdlGenerator
from aclimatise.model import CliArgument, Flag, SimpleFlagArg
from aclimatise.yaml import yaml

from .util import convert_validate, skip_not_installed

# Note: the parse and explore tests run conversion tests already. These tests are for specific edge cases


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


def test_docker_conversion(bedtools_cmd):
    intersect = bedtools_cmd["intersect"]
    container = "quay.io/biocontainers/bedtools:2.29.2--hc088bd4_0"
    intersect.docker_image = container
    with tempfile.NamedTemporaryFile() as cwl_file:
        CwlGenerator().save_to_file(intersect, path=Path(cwl_file.name))
        cwl_file.seek(0)
        parsed_cwl = yaml.load(cwl_file)
        assert any(
            [
                hint["class"] == "DockerRequirement" and hint["dockerPull"] == container
                for hint in parsed_cwl["hints"]
            ]
        )

    wdl = WdlGenerator().save_to_string(intersect)
    parsed_wdl = parse_document(wdl).tasks[0]
    assert parsed_wdl.runtime["docker"].literal.value == container


@pytest.mark.parametrize(
    "flag,cwltype,wdltype",
    [
        [
            Flag(
                synonyms=["--some-flag"],
                optional=True,
                args=SimpleFlagArg("string"),
                description="",
            ),
            "string?",
            "String?",
        ],
        [
            Flag(
                synonyms=["--some-flag"],
                optional=False,
                args=SimpleFlagArg("string"),
                description="",
            ),
            "string",
            "String",
        ],
    ],
)
def test_types_conversion(flag: CliArgument, cwltype: str, wdltype: str):
    """
    Test that types are being correctly translated from aCLImatise types to CWL and WDL
    """
    assert CwlGenerator.arg_to_cwl_type(flag) == cwltype
    assert (
        WdlGenerator.type_to_wdl(flag.get_type(), optional=flag.optional).get_string()
        == wdltype
    )
