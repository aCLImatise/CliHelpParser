import pytest

from acclimatise.cli_types import CliBoolean, CliDir, CliFile, CliFloat, CliInteger, CliOutputDir, CliOutputFile, CliString
from acclimatise.model import infer_type


@pytest.mark.parametrize(
    "string,typ",
    [("", CliString),
     ("int", CliInteger),
     ("size", CliInteger),
     ("length", CliInteger),
     ("max", CliInteger),
     ("min", CliInteger),
     ("str", CliString),
     ("float", CliFloat),
     ("decimal", CliFloat),
     ("bool", CliBoolean),
     ("file", CliFile),
     ("path", CliFile),
     ("input file", CliFile),
     ("output file", CliOutputFile),
     ("folder", CliDir),
     ("directory", CliDir),
     ("output directory", CliOutputDir)])
def test_type_inference(string, typ):
    assert isinstance(infer_type(string), typ)
