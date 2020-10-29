import random
import string

import pytest
from pkg_resources import resource_filename

from aclimatise.integration import parse_help

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

    # Check that the help text is included in the command
    assert cmd.help_text == help_text

    test.run_assertions(cmd, explore=False)


@pytest.mark.timeout(20)
def test_long_text():
    """
    This tests the case where the parse function is handed an inordinate amount of text. In this case, we shouldn't
    bother parsing, and just return an empty command
    """
    text = "\n".join(
        [
            "".join(
                random.choices(
                    string.ascii_letters + " ",
                    weights=[1] * len(string.ascii_letters) + [5],
                    k=100,
                )
            )
            for i in range(2000)
        ]
    )
    command = parse_help(["some", "command"], text=text)
    assert len(command.positional) == 0
    assert len(command.named) == 0
