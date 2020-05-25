"""
Test data model methods
"""
from acclimatise.model import EmptyFlagArg, Flag, Positional


def test_name_to_words_symbol():
    """
    Check that we can get an argument name even if the argument's flag is a symbol
    """
    arg = Flag(
        synonyms=["-@"],
        description="Number of additional threads to use",
        args=EmptyFlagArg(),
    )

    assert list(arg._name_from_name()) == ["at"]


def test_name_to_words():
    """
    Check that we can get an argument name even if the argument's flag is a symbol
    """
    arg = Flag(synonyms=["--genomepaths"], description="", args=EmptyFlagArg(),)

    assert list(arg._name_from_name()) == ["genome", "paths"]


def test_bwa_mem_infq():
    arg = Positional(name="in1.fq", description="", position=0)
    name = arg.variable_name([])
    assert "1" in name or "one" in name
    assert "in" in name
    assert "fq" in name
