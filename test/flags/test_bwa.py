import shutil
from textwrap import dedent

import pytest

from acclimatise import parse_help
from acclimatise.flag_parser import elements
from acclimatise.model import Flag, FlagSynonym, OptionalFlagArg


def test_flag_arg(parser):
    result = elements.flag_with_arg.parseString("-A INT")[0]
    assert isinstance(result, FlagSynonym)
    assert result.argtype.name == "INT"
    assert result.name == "-A"


def test_flag(parser):
    result = parser.flag.parseString(
        "-A INT        score for a sequence match, which scales options -TdBOELU unless overridden [1]"
    )[0]
    assert isinstance(result, Flag)
    assert result.synonyms[0] == "-A"
    assert result.args.name == "INT"


def test_flag_b(parser):
    result = parser.flag.parseString("-B INT        penalty for a mismatch [4]")
    print(result)


def test_multiarg_flag(parser):
    result = parser.flag.parseString(
        "-O INT[,INT]  gap open penalties for deletions and insertions [6,6]"
    )[0]
    assert isinstance(result, Flag)


def test_flags(parser):
    result = parser.flags.parseString(
        """
       -A INT        score for a sequence match, which scales options -TdBOELU unless overridden [1]
       -B INT        penalty for a mismatch [4]
    """,
        parseAll=True,
    )


def test_bwa_segmented_options(parser):
    result = parser.flag_block.parseString(
        """
       -A INT        score for a sequence match, which scales options -TdBOELU unless overridden [1]
       -B INT        penalty for a mismatch [4]
       -O INT[,INT]  gap open penalties for deletions and insertions [6,6]
       -E INT[,INT]  gap extension penalty; a gap of size k cost '{-O} + {-E}*k' [1,1]
       -L INT[,INT]  penalty for 5'- and 3'-end clipping [5,5]
       -U INT        penalty for an unpaired read pair [17]

       -x STR        read type. Setting -x changes multiple parameters unless overriden [null]
                     pacbio: -k17 -W40 -r10 -A1 -B1 -O1 -E1 -L0  (PacBio reads to ref)
                     ont2d: -k14 -W20 -r10 -A1 -B1 -O1 -E1 -L0  (Oxford Nanopore 2D-reads to ref)
                     intractg: -B9 -O16 -L5  (intra-species contigs to ref)
    """,
        parseAll=True,
    )
    assert len(result) == 7


def test_bwa_help_part(parser):
    results = list(
        parser.flags.scanString(
            """
Algorithm options:

       -t INT        number of threads [1]
       -k INT        minimum seed length [19]
       -w INT        band width for banded alignment [100]
       -d INT        off-diagonal X-dropoff [100]
       -r FLOAT      look for internal seeds inside a seed longer than {-k} * FLOAT [1.5]
       -y INT        seed occurrence for the 3rd round seeding [20]
       -c INT        skip seeds with more than INT occurrences [500]
       -D FLOAT      drop chains shorter than FLOAT fraction of the longest overlapping chain [0.50]
       -W INT        discard a chain if seeded bases shorter than INT [0]
       -m INT        perform at most INT rounds of mate rescues for each read [50]
       -S            skip mate rescue
       -P            skip pairing; mate rescue performed unless -S also in use
    """
        )
    )
    assert len(results) == 1

    for tokens, start, end in results:
        assert len(tokens) == 12


def test_bwa_multisection(parser):
    s = """
Scoring options:

       -x STR        read type. Setting -x changes multiple parameters unless overriden [null]
                     pacbio: -k17 -W40 -r10 -A1 -B1 -O1 -E1 -L0  (PacBio reads to ref)
                     ont2d: -k14 -W20 -r10 -A1 -B1 -O1 -E1 -L0  (Oxford Nanopore 2D-reads to ref)
                     intractg: -B9 -O16 -L5  (intra-species contigs to ref)

Input/output options:

       -p            smart pairing (ignoring in2.fq)
    """
    result_lists = list(parser.flags.scanString(s))
    assert len(result_lists) == 2
    for result_list, b, c in result_lists:
        assert len(result_list) == 1


def test_complex_optionals(parser):
    s = """
       -I FLOAT[,FLOAT[,INT[,INT]]]
                     specify the mean, standard deviation (10% of the mean if absent), max
                     (4 sigma from the mean if absent) and min of the insert size distribution.
                     FR orientation only. [inferred]
    """
    results = list(parser.flag_block.parseString(s))[0]
    assert isinstance(results, Flag)
    assert isinstance(results.args, OptionalFlagArg)
    assert results.args.names == ["FLOAT", "FLOAT", "INT", "INT"]


def test_bwa_skipping(parser):
    s = """
Input/output options:

       -p            smart pairing (ignoring in2.fq)
       -R STR        read group header line such as '@RG\tID:foo\tSM:bar' [null]
       -H STR/FILE   insert STR to header if it starts with @; or insert lines in FILE [null]
       -o FILE       sam file to output results to [stdout]
       -j            treat ALT contigs as part of the primary assembly (i.e. ignore <idxbase>.alt file)
       -5            for split alignment, take the alignment with the smallest coordinate as primary
     """
    cmd = parser.parse_command(cmd=s, name=["bwa", "mem"])
    assert len(cmd.named) == 6


def test_bwa_root(bwa_help):
    command = parse_help(["bwa"], bwa_help)
    assert len(command.named) == 0
    assert len(command.positional) == 14
    assert command.positional[0].name == "index"
    assert command.positional[-1].name == "bwt2sa"


def test_bwa(parser, bwamem_help):
    # Parse help
    command = parse_help(["bwa", "mem"], text=bwamem_help)

    assert len(command.named) == 36
    assert len(command.positional) == 3
