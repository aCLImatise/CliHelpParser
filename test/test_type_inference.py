import pytest

from acclimatise.cli_types import CliBoolean, CliDir, CliFile, CliFloat, CliInteger, CliString
from acclimatise.model import infer_type


@pytest.mark.parametrize(
    "string,typ,isoutput",
    [("", CliString, False),
     ("int", CliInteger, False),
     ("size", CliInteger, False),
     ("length", CliInteger, False),
     ("max", CliInteger, False),
     ("min", CliInteger, False),
     ("str", CliString, False),
     ("float", CliFloat, False),
     ("decimal", CliFloat, False),
     ("bool", CliBoolean, False),
     ("file", CliFile, False),
     ("path", CliFile, False),
     ("input file", CliFile, False),
     ("output file", CliFile, True),
     ("folder", CliDir, False),
     ("directory", CliDir, False),
     ("output directory", CliDir, True)])
def test_type_inference(string, typ, isoutput):
    inferred_type = infer_type(string)
    assert isinstance(inferred_type, typ)
    assert not hasattr(inferred_type, "output") or inferred_type.output == isoutput
