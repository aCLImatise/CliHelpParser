import pytest

from aclimatise.cli_types import (
    CliBoolean,
    CliDir,
    CliFile,
    CliFloat,
    CliInteger,
    CliString,
    CliType,
)
from aclimatise.model import CliArgument, EmptyFlagArg, Flag, SimpleFlagArg, infer_type


@pytest.mark.parametrize(
    "string,typ",
    [
        ("", None),
        ("int", CliInteger()),
        ("size", CliInteger()),
        ("length", CliInteger()),
        ("max", CliInteger()),
        ("min", CliInteger()),
        ("str", CliString()),
        ("float", CliFloat()),
        ("decimal", CliFloat()),
        ("bool", CliBoolean()),
        ("file", CliFile()),
        ("path", CliFile()),
        ("input file", CliFile(output=False)),
        ("output file", CliFile(output=True)),
        ("folder", CliDir()),
        ("directory", CliDir()),
        ("output directory", CliDir(output=True)),
        ("blah 23 blub", CliInteger()),
        ("nonsense 23.42", CliFloat()),
        (".42 gibberish", CliFloat()),
        ("1E-5", CliFloat()),
        ("BOOL Output strand bias files, 'true' or 'false'", CliBoolean()),
        ("file to write out dict file [stdout]", CliFile(output=True)),
        ("Filename to output the counts to instead of stdout.", CliFile(output=True)),
        pytest.param(
            "Write out all SAM alignment records into SAM/BAM files (one per input file needed), annotating each line with its feature assignment (as an optional field with tag 'XF'). See the -p option to use BAM instead of SAM.",
            CliFile(output=True),
            marks=pytest.mark.xfail(
                reason="This description doesn't make it clear that it wants an output file. I'm not sure how this could ever be parsed"
            ),
        ),
    ],
)
def test_type_inference(string, typ):
    inferred_type = infer_type(string)
    assert inferred_type == typ


@pytest.mark.parametrize(
    "flag,typ",
    [
        [
            Flag(
                description="Filename to output the counts to instead of stdout.",
                synonyms=["-c", "--counts_output"],
                args=SimpleFlagArg("OUTPUT_FILENAME"),
            ),
            CliFile(output=True),
        ],
        pytest.param(
            Flag(
                description="redirect output to specified file\ndefault: undefined",
                synonyms=["-o"],
                args=EmptyFlagArg(),
            ),
            CliFile(output=True),
            marks=pytest.mark.xfail(
                reason="Because the help doesn't indicate an argument, we can't know that this is an output file"
            ),
        ),
    ],
)
def test_flag_type_inference(flag: CliArgument, typ: CliType):
    inferred_type = flag.get_type()
    assert inferred_type == typ
