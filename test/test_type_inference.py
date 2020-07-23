from acclimatise.cli_types import CliString
from acclimatise.model import infer_type


def test_type_inference():
    test_strings = [("", CliString, False), ("int", CliInteger, False),
                    ("size", CliInteger, False), ("length", CliInteger, False),
                    ("max", CliInteger, False), ("min", CliInteger, False),
                    ("str", CliString, False), ("float", CliFloat, False),
                    ("decimal", CliFloat, False), ("bool", CliBoolean, False),
                    ("file", CliFile, False), ("path", CliFile, False),
                    ("input file", CliFile, False),
                    ("output file", CliFile, True), ("folder", CliDir, False),
                    ("directory", CliDir, False),
                    ("output directory", CliDir, False)]

    for ts in test_strings:
        typ = infer_type(ts[0])
        assert isinstance(typ, ts[1]), "%s should be %s but is %s" % (ts[0], ts[1], typ)
        assert not typ.hasattr("output") or typ.output == ts[2]
