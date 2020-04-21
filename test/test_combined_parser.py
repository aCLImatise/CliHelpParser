from acclimatise import parse_help


def test_pisces(pisces_help):
    command = parse_help(cmd=["pisces"], text=pisces_help)
    assert len(command.named) == 57


def test_htseq(htseq_help):
    command = parse_help(cmd=["htseq-count"], text=htseq_help)
    assert len(command.named) == 14
    assert len(command.positional) == 2


def test_bwa(bwamem_help):
    command = parse_help(cmd=["bwa", "mem"], text=bwamem_help)
    assert len(command.named) == 32
    assert len(command.positional) == 3


def test_podchecker(podchecker_help):
    command = parse_help(cmd=["podchecker"], text=podchecker_help)
    assert len(command.named) == 2
    assert len(command.positional) == 1
