from acclimatise.parser import parse_help


def test_pisces(pisces_help):
    command = parse_help(cmd=['pisces'], text=pisces_help)
    assert len(command.named) == 57


def test_htseq(htseq_help):
    command = parse_help(cmd=['htseq-counts'], text=htseq_help)
    assert len(command.named) == 57


def test_bwa(bwamem_help):
    command = parse_help(cmd=['bwa', 'mem'], text=bwamem_help)
    assert len(command.named) == 57
