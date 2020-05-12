"""
Test data model methods
"""
from acclimatise.model import EmptyFlagArg, Flag


def test_name_to_words_symbol():
    """
    Check that we can get an argument name even if the argument's flag is a symbol
    """
    arg = Flag(
        synonyms=["-@"],
        description="Number of additional threads to use",
        args=EmptyFlagArg(),
    )

    assert list(arg.name_to_words()) == ["commercial", "at"]


def test_name_to_words():
    """
    Check that we can get an argument name even if the argument's flag is a symbol
    """
    arg = Flag(synonyms=["--genomepaths"], description="", args=EmptyFlagArg(),)

    assert list(arg.name_to_words()) == ["genome", "paths"]
