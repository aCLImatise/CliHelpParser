"""
Test the casing (snake_case vs camelCase) used by the converters
"""
import pytest

from aclimatise.converter import WrapperGenerator
from aclimatise.model import EmptyFlagArg, Flag


def test_camel_short(camel_gen):
    flag = Flag(
        synonyms=["-t"], description="number of threads [1]", args=EmptyFlagArg()
    )
    names = camel_gen.choose_variable_names([flag], length=3)
    assert names[0].name == "numberOfThreads"


def test_snake_short(snake_gen):
    flag = Flag(
        synonyms=["-t"], description="number of threads [1]", args=EmptyFlagArg()
    )
    names = snake_gen.choose_variable_names([flag], length=2)
    assert "number" in names[0].name
    assert "threads" in names[0].name


def test_camel_long(camel_gen):
    flag = Flag(
        synonyms=["-g", "--genomepaths", "--genomefolders"],
        description="number of threads [1]",
        args=EmptyFlagArg(),
    )
    names = camel_gen.choose_variable_names([flag], length=2)
    assert names[0].name == "genomeFolders"


def test_snake_long(snake_gen):
    flag = Flag(
        synonyms=["-g", "--genomepaths", "--genomefolders"],
        description="number of threads [1]",
        args=EmptyFlagArg(),
    )
    names = snake_gen.choose_variable_names([flag], length=2)
    assert names[0].name == "genome_folders"
