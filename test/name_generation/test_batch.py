import tempfile
from itertools import product

import pytest
from pkg_resources import resource_filename

from acclimatise import WrapperGenerator, parse_help
from acclimatise.name_generation import generate_names

from ..util import HelpText, all_tests, convert_validate, validate_cwl, validate_wdl


@pytest.mark.parametrize("test", all_tests)
def test_all(test: HelpText):
    """
    Tests that generate_names can work on real-life Commands without exceeding reasonable system resources
    """
    with open(resource_filename("test", test.path)) as fp:
        help_text = fp.read()

    cmd = parse_help(test.cmd, help_text)

    generate_names([arg.description for arg in [*cmd.positional, *cmd.named]])
