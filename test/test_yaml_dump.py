from io import StringIO

from acclimatise import parse_help
from acclimatise.yaml import yaml


def test_round_trip(bwamem_help):
    command = parse_help(["bwa", "mem"], bwamem_help)

    # Dump
    buffer = StringIO()
    yaml.dump(command, buffer)

    # Load
    buffer.seek(0)
    output = yaml.load(buffer)

    # Assert the round trip worked
    assert command == output
