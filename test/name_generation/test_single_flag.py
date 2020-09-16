"""
Tests for the name generation of single flags
"""
from aclimatise.converter.wdl import WdlGenerator
from aclimatise.model import EmptyFlagArg, Flag, Positional, SimpleFlagArg


def test_samtools_dict_output():
    gen = WdlGenerator()
    arg = Flag(
        synonyms=["-o", "--output"],
        description="file to write out dict file [stdout]",
        args=SimpleFlagArg(name="str"),
    )
    name = gen.choose_variable_names([arg])[0].name
    # The WDL converter should avoid naming a variable "output" since that's a WDL keyword
    assert name != "output"

    # Also, since we have a description, the generator shouldn't choose the lazy option of var_output
    assert name != "var_output"


def test_samtools_quickcheck_output():
    gen = WdlGenerator()
    arg = Positional(description="", position=0, name="input")
    name = gen.choose_variable_names([arg])[0].name
    # The WDL converter should avoid naming a variable "output" since that's a WDL keyword
    assert name != "input"


def test_bwt2sa_i(gen):
    arg = Flag(synonyms=["-i"], description="", args=SimpleFlagArg(name="32"))

    name = gen.choose_variable_names([arg])[0].name
    # 32 isn't a valid variable name, so the only option here is to use the letter i
    assert name == "i"


def test_name_to_words_symbol(gen):
    """
    Check that we can get an argument name even if the argument's flag is a symbol
    """
    arg = Flag(
        synonyms=["-@"],
        description="Number of additional threads to use",
        args=EmptyFlagArg(),
    )

    name = gen.choose_variable_names([arg])[0].name
    assert name == "at"


def test_name_to_words(gen):
    """
    Check that we can get an argument name even if the argument's flag is a symbol
    """
    arg = Flag(
        synonyms=["--genomepaths"],
        description="",
        args=EmptyFlagArg(),
    )

    name = gen.choose_variable_names([arg])[0].name
    assert "genome" in name
    assert "paths" in name
    # assert list(arg._name_from_name()) == ["genome", "paths"]


def test_bwa_mem_infq(gen):
    arg = Positional(name="in1.fq", description="", position=0)
    name = gen.choose_variable_names([arg])[0].name
    # name = arg.variable_name([])
    assert "1" in name or "one" in name
    assert "in" in name
    assert "fq" in name
