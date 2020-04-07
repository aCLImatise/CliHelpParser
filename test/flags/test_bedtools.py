def test_bedtools_root(parser, bedtools_help):
    command = parser.parse_command(bedtools_help, ["bedtools"])
    assert len(command.named) == 1
    assert len(command.positional) == 43
