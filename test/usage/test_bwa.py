from acclimatise.usage_parser.elements import usage, usage_element, short_flag_list


def test_bwa():
    txt = "Usage: bwa mem [options] <idxbase> <in1.fq> [in2.fq]"
    els = usage.parseString(txt)
    print(els)


def test_samtools_merge_short_flags():
    text = "-nurlf"
    short_flag_list.parseString(text)


def test_samtools_merge_optional_short_flags():
    text = "[-nurlf]"
    usage_element.parseString(text)


def test_samtools_merge_full():
    text = "Usage: samtools merge [-nurlf] [-h inh.sam] [-b <bamlist.fofn>] <out.bam> <in1.bam> [<in2.bam> ... <inN.bam>]"
    els = usage.parseString(text)
    print(els)
