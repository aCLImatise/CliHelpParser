from acclimatise.model import Flag


def test_podchecker_flags(parser):
    cmd = """
        -warnings -nowarnings
            Turn on/off printing of warnings. Repeating -warnings increases
            the warning level, i.e. more warnings are printed. Currently
            increasing to level two causes flagging of unescaped "<,>"
            characters.
    """
    flag = parser.flag_block.parseString(cmd)
    assert isinstance(flag[0], Flag)
    assert len(flag[0].synonyms) == 2


def test_podchecker(podchecker_help, parser):
    cmd = """
Options and Arguments:
    -help   Print a brief help message and exit.

    -man    Print the manual page and exit.

    -warnings -nowarnings
            Turn on/off printing of warnings. Repeating -warnings increases
            the warning level, i.e. more warnings are printed. Currently
            increasing to level two causes flagging of unescaped "<,>"
            characters.

    file    The pathname of a POD file to syntax-check (defaults to standard
            input).
"""
    flags = parser.flags.searchString(cmd)[0]
    assert len(flags) == 4
