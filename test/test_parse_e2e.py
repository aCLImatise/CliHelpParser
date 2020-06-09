import tempfile
from itertools import product

import pytest
from pkg_resources import resource_filename

from acclimatise import parse_help

from .util import (
    HelpText,
    all_ids,
    all_tests,
    all_tests_lookup,
    convert_validate,
    validate_cwl,
    validate_wdl,
)


@pytest.mark.parametrize("test", all_tests, ids=all_ids)
def test_all(test: HelpText):
    """
    A comprehensive end-to-end test that tests the parser and converters, using the test data files
    """
    with open(resource_filename("test", test.path)) as fp:
        help_text = fp.read()

    cmd = parse_help(test.cmd, help_text)

    # Check we parsed the arguments correctly
    # Since we aren't exploring here, we can't distinguish between positionals and subcommands, so we can sum them
    assert len(cmd.positional) == test.positional + test.subcommands
    assert len(cmd.named) == test.named

    # Check that the help text is included in the command
    assert cmd.help_text == help_text

    # Check the converters work
    convert_validate(cmd, explore=False)
