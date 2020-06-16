from .util import convert_validate


def test_premade_samtools(samtools_cmd):
    """
    Use a command tree that was generated beforehand, to quickly detect issues relating to the conversion of command
    trees
    """
    convert_validate(samtools_cmd, explore=True)


def test_premade_bedtools(bedtools_cmd):
    """
    Use a command tree that was generated beforehand, to quickly detect issues relating to the conversion of command
    trees
    """
    convert_validate(bedtools_cmd, explore=True)
