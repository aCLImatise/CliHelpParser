from aclimatise.model import Command


def test_reanalyse(samtools_cmd: Command):
    """
    Test the command.reanalyse() method
    """
    reanalysed = samtools_cmd.reanalyse()
    assert reanalysed.help_text == samtools_cmd.help_text
    assert len(reanalysed.subcommands) == len(samtools_cmd.subcommands)

    re_sort = reanalysed["sort"]
    assert len(re_sort.positional) > 0
    assert len(re_sort.named) > 0
