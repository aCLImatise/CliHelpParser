"""
Test all the test data files
"""
import pytest
from pkg_resources import resource_filename

from aclimatise import WrapperGenerator, parse_help

from ..util import HelpText, all_tests, convert_validate, validate_cwl, validate_wdl


@pytest.mark.parametrize("test", all_tests)
def test_all(test: HelpText):
    """
    Tests that generate_names can work on real-life Commands without exceeding reasonable system resources
    """
    with open(resource_filename("test", test.path)) as fp:
        help_text = fp.read()

    cmd = parse_help(test.cmd, help_text)

    WrapperGenerator().choose_variable_names([*cmd.positional, *cmd.named])
