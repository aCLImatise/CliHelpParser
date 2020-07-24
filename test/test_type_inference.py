import pytest

from acclimatise.cli_types import CliString
from acclimatise.model import infer_type


@pytest.mark.parametrize(
    "string,typ,isoutput",
    [("", CliString, False), ("int", CliInteger, False),
     ("size", CliInteger, False), ("length", CliInteger, False),
     ("max", CliInteger, False), ("min", CliInteger, False),
     ("str", CliString, False), ("float", CliFloat, False),
     ("decimal", CliFloat, False), ("bool", CliBoolean, False),
     ("file", CliFile, False), ("path", CliFile, False),
     ("input file", CliFile, False),
     ("output file", CliFile, True), ("folder", CliDir, False),
     ("directory", CliDir, False),
     ("output directory", CliDir, False)])
def test_type_inference(string, typ, isoutput):
    result_typ = infer_type(string)
    assert isinstance(result_typ, typ)
    assert not result_typ.hasattr("output") or result_typ.output == isoutput
