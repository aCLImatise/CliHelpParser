"""
Tests certain groups of flags used together
"""
from acclimatise.converter import WrapperGenerator
from acclimatise.model import EmptyFlagArg, Flag, SimpleFlagArg


def test_bedtools_window_sm():
    """
    These two flags have almost the same name, and almost the same description
    """
    flags = [
        Flag(
            synonyms=["-sm"],
            description="Only report hits in B that overlap A on the _same_ strand.",
            args=EmptyFlagArg(),
        ),
        Flag(
            synonyms=["-sm"],
            description="Only report hits in B that overlap A on the _opposite_ strand.",
            args=EmptyFlagArg(),
        ),
        Flag(
            synonyms=["-c"],
            description="For each entry in A, report the number of overlaps with B.",
            args=EmptyFlagArg(),
        ),
    ]
    args = WrapperGenerator().choose_variable_names(flags)
    assert len(set([arg.name for arg in args])) == 3


def test_same_description():
    """
    Normally we ignore one-character flag names, and instead try to read their descriptions for a more informative name.
    However, if the descriptions are identical to each other, we have to fall back to the description
    """
    flags = [
        Flag(
            synonyms=["-a"],
            description="Makes the program do a certain thing",
            args=EmptyFlagArg(),
        ),
        Flag(
            synonyms=["-b"],
            description="Makes the program do a certain thing",
            args=EmptyFlagArg(),
        ),
    ]
    names = WrapperGenerator().choose_variable_names(flags)
    assert names[0].name == "a"
    assert names[1].name == "b"


def test_same_arg():
    """
    Normally we ignore one-character flag names, and instead try to read their descriptions for a more informative name.
    However, if the descriptions are identical to each other, we have to fall back to the description
    """
    flags = [
        Flag(synonyms=["-a"], description="", args=SimpleFlagArg("SomeThing")),
        Flag(synonyms=["-b"], description="", args=SimpleFlagArg("SomeThing")),
    ]
    names = WrapperGenerator().choose_variable_names(flags)
    assert names[0].name == "a"
    assert names[1].name == "b"
