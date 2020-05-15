import tempfile
from itertools import product

import pytest
from pkg_resources import resource_filename

from acclimatise import WrapperGenerator, parse_help

from .util import HelpText, all_tests, validate_cwl, validate_wdl


@pytest.mark.parametrize(
    ["test", "language_data"],
    list(product(all_tests, [["cwl", validate_cwl], ["wdl", validate_wdl]])),
)
def test_all(test: HelpText, language_data):
    """
    A comprehensive end-to-end test that tests the parser and converters, using the test data files
    """
    language, validate = language_data
    with open(resource_filename("test", test.path)) as fp:
        help_text = fp.read()

    cmd = parse_help(test.cmd, help_text)

    # Check we parsed the arguments correctly
    assert len(cmd.positional) == test.positional
    assert len(cmd.named) == test.named

    # Check that the help text is included in the command
    assert cmd.help_text == help_text

    # Check the converters work
    converter = WrapperGenerator.choose_converter(language)()
    converted = converter.generate_wrapper(cmd)
    validate(converted)
