from acclimatise.usage_parser.elements import usage, usage_element, short_flag_list, short_flag
from acclimatise.usage_parser.model import UsageElement
from acclimatise.model import Flag, SimpleFlagArg


def test_bwa():
    txt = "Usage: bwa mem [options] <idxbase> <in1.fq> [in2.fq]"
    els = usage.parseString(txt)
    print(els)


def test_samtools_merge_short_flags():
    text = "-nurlf"
    els = short_flag_list.parseString(text)
    assert len(els) == 5
    assert isinstance(els[0], Flag)


def test_samtools_merge_optional_short_flags():
    text = "[-nurlf]"
    els = usage_element.parseString(text)
    assert len(els) == 5
    assert isinstance(els[0], Flag)
    assert els[0].optional


def test_samtools_merge_variable():
    text = "<out.bam>"
    els = usage_element.parseString(text)
    assert len(els) == 1
    assert isinstance(els[0], UsageElement)
    assert els[0].variable


def test_samtools_merge_flag_arg():
    text = "-h inh.sam"
    els = usage_element.parseString(text)
    assert len(els) == 1
    assert isinstance(els[0], Flag)
    assert isinstance(els[0].args, SimpleFlagArg)


def test_samtools_merge_optional_flag_arg():
    text = "[-h inh.sam]"
    els = usage_element.setDebug(True).parseString(text)
    assert len(els) == 1
    assert isinstance(els[0], Flag)
    assert els[0].optional
    assert isinstance(els[0].args, SimpleFlagArg)


def test_samtools_merge_full():
    text = "Usage: samtools merge [-nurlf] [-h inh.sam] [-b <bamlist.fofn>] <out.bam> <in1.bam> [<in2.bam> ... <inN.bam>]"
    els = usage.parseString(text)
    print(els)
