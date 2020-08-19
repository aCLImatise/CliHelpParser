import pytest

from acclimatise.flag_parser.elements import (
    arg_expression,
    flag_with_arg,
    list_type_arg,
)
from acclimatise.model import Flag, RepeatFlagArg, SimpleFlagArg
from acclimatise.usage_parser import parse_usage
from acclimatise.usage_parser.elements import (  # short_flag_list,
    stack,
    usage,
    usage_element,
)
from acclimatise.usage_parser.model import UsageElement


def test_bwa():
    txt = "Usage: bwa mem [options] <idxbase> <in1.fq> [in2.fq]"
    els = usage.parseString(txt)
    print(els)


@pytest.mark.skip(
    "It's impossible to distinguish between a grouped list of short flags and one long flag with a single dash"
)
def test_samtools_merge_short_flags():
    text = "-nurlf"
    els = short_flag_list.parseString(text)
    assert len(els) == 5
    assert isinstance(els[0], Flag)


@pytest.mark.skip(
    "It's impossible to distinguish between a grouped list of short flags and one long flag with a single dash"
)
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
    els = usage_element.setDebug().parseString(text)
    assert len(els) == 1
    assert isinstance(els[0], Flag)
    assert els[0].optional
    assert isinstance(els[0].args, SimpleFlagArg)


def test_samtools_merge_list_args():
    text = "[<in2.bam> ... <inN.bam>]"
    el = usage_element.parseString(text)
    assert len(el) == 1
    assert isinstance(el[0], UsageElement)
    assert el[0].repeatable


def test_samtools_merge_full(process):
    text = process(
        """
    Usage: samtools merge [-nurlf] [-h inh.sam] [-b <bamlist.fofn>] <out.bam> <in1.bam> [<in2.bam> ... <inN.bam>]
    """
    )
    command = parse_usage(cmd=["samtools", "merge"], text=text)

    assert len(command.positional) == 3
    assert command.positional[0].name == "out.bam"
    assert command.positional[1].name == "in1.bam"

    assert len(command.named) == 3
    assert command.named[0].longest_synonym == "-nurlf"
    assert command.named[1].longest_synonym == "-h"
    assert command.named[2].longest_synonym == "-b"


def test_pisces_usage():
    text = "USAGE: dotnet Pisces.dll -bam <bam path> -g <genome path>"
    command = parse_usage(["pisces"], text)
    assert len(command.named) == 2
    assert len(command.positional) == 0
    assert command.named[0].longest_synonym == "-bam"
    assert command.named[1].longest_synonym == "-g"


def test_trailing_text(process):
    """
    Tests that the usage parser will not parse text after the usage section has ended
    """
    text = process(
        """
    usage: htseq-count [options] alignment_file gff_file

    This script takes one or more alignment files in SAM/BAM format and a feature
    file in GFF format and calculates for each feature the number of reads mapping
    to it. See http://htseq.readthedocs.io/en/master/count.html for details.
    """
    )
    command = parse_usage(["htseq-count"], text)
    # We don't count either the command "htseq-count", or "[options]" as an argument, so there are only 2 positionals
    assert len(command.positional) == 2


def test_bwt2sa():
    text = """
Usage: bwa bwt2sa [-i 32] <in.bwt> <out.sa>
    """

    command = parse_usage(["bwa", "bwt2sa"], text)

    # in and out
    assert len(command.positional) == 2

    # -i
    assert len(command.named) == 1


def test_bedtools_multiinter_flag_arg():
    text = " FILE1 FILE2 .. FILEn"
    arg = arg_expression.parseString(text)[0]
    assert isinstance(arg, RepeatFlagArg)
    assert arg.name == "FILEn"


def test_bedtools_multiinter_flag():
    text = "-i FILE1 FILE2 .. FILEn"
    arg = flag_with_arg.parseString(text)[0]
    assert isinstance(arg.argtype, RepeatFlagArg)
    assert arg.name == "-i"


def test_bedtools_multiinter():
    text = """
Summary: Identifies common intervals among multiple
	 BED/GFF/VCF files.

Usage:   bedtools multiinter [OPTIONS] -i FILE1 FILE2 .. FILEn
	 Requires that each interval file is sorted by chrom/start. 

Options: 
	-cluster	Invoke Ryan Layers's clustering algorithm.
    """

    command = parse_usage(["bedtools", "multiinter"], text)

    assert len(command.positional) == 0
    assert len(command.named) == 1
    assert command.named[0].longest_synonym == "-i"
    assert isinstance(command.named[0].args, RepeatFlagArg)


def test_samtools_dict():
    text = """
Usage:   samtools dict [options] <file.fa|file.fa.gz>
    """
    command = parse_usage(["samtools", "dict"], text, debug=True)
    assert len(command.positional) == 1


def test_mid_line_usage():
    text = """
    Can't open --usage: No such file or directory at /usr/bin/samtools.pl line 50.
    """
    command = parse_usage(["samtools.pl", "showALEN"], text, debug=True)
    assert command.empty
