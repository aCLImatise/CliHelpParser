from acclimatise.model import Flag


def test_unindented_flags(parser):
    """
    Verify that we can parse blocks of flags that aren't intended (which is unusual)
    """

    text = """
-genomic          specify input files containing genomic sequences
                  mandatory option
-cdna             specify input files containing cDNA/EST sequences
-protein          specify input files containing protein sequences
    """.strip()
    flags = parser.flag_block.parseString(text)
    assert len(flags) == 3
    for flag in flags:
        assert isinstance(flag, Flag)
