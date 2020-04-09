def test_bedtools_block(parser, process):
    txt = """
[ Multi-way file comparisons ]
    multiinter    Identifies common intervals among multiple interval files.
    unionbedg     Combines coverage intervals from multiple BEDGRAPH files.

[ Paired-end manipulation ]
    """
    blocks = parser.flags.searchString(txt)
    assert len(blocks) == 1, "This comprises only one block of flags"
    assert len(blocks[0]) == 2, "The single block contains 2 positional arguments"


def test_bedtools_root(parser, bedtools_help):
    command = parser.parse_command(bedtools_help, ["bedtools"])
    assert len(command.named) == 1
    assert len(command.positional) == 43
