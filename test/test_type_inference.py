import pytest

from acclimatise.cli_types import (
    CliBoolean,
    CliDir,
    CliFile,
    CliFloat,
    CliInteger,
    CliString,
)
from acclimatise.model import infer_type


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
    ],
)
def test_type_inference(string, typ):
    inferred_type = infer_type(string)
    assert inferred_type == typ
