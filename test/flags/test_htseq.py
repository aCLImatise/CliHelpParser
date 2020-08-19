"""
Uses htseq-count, which is used as an example of a Python argparse CLI
"""
import shutil
from textwrap import dedent

import pytest

from acclimatise.flag_parser import elements
from acclimatise.model import EmptyFlagArg, FlagSynonym, RepeatFlagArg


def test_short(parser):
    flag = elements.flag_with_arg.parseString(
        dedent(
            """
        -i IDATTR
        """
        )
    )[0]
    assert isinstance(flag, FlagSynonym)


def test_long_short_synonyms(parser):
    flag = elements.flag_synonyms.parseString(
        dedent(
            """
        -i IDATTR, --idattr IDATTR
        """
        )
    )[0]
    print(flag)


def test_long_short_desc(parser):
    flag = parser.flag.parseString(
        dedent(
            """
        -i IDATTR, --idattr IDATTR
                          GFF attribute to be used as feature ID (default,
                          suitable for Ensembl GTF files: gene_id)
        """
        )
    )[0]
    print(flag)


def test_long_short_choices(parser):
    flag = parser.flag.parseString(
        dedent(
            """
          -m {union,intersection-strict,intersection-nonempty}, --mode {union,intersection-strict,intersection-nonempty}
                                mode to handle reads overlapping more than one feature
                                (choices: union, intersection-strict, intersection-
                                nonempty; default: union)
        """
        )
    )


def test_help_section_preamble(parser):
    flags = list(
        parser.flags.searchString(
            dedent(
                """
optional arguments:
  -h, --help            show this help message and exit
  -f {sam,bam}, --format {sam,bam}
                        type of <alignment_file> data, either 'sam' or 'bam'
                        (default: sam)
        """
            )
        )
    )[0]
    assert len(flags) == 2


def test_repeat_type(parser):
    flag = elements.flag_synonyms.parseString(
        "--additional-attr ADDITIONAL_ATTR [ADDITIONAL_ATTR ...]"
    )[0]
    assert flag.name == "--additional-attr"
    assert isinstance(flag.argtype, RepeatFlagArg)
    assert flag.argtype.name == "ADDITIONAL_ATTR"


def test_full_flags(parser):
    results = parser.flag.scanString(
        dedent(
            """
  -h, --help            show this help message and exit
  -f {sam,bam}, --format {sam,bam}
                        type of <alignment_file> data, either 'sam' or 'bam'
                        (default: sam)
  -r {pos,name}, --order {pos,name}
                        'pos' or 'name'. Sorting order of <alignment_file>
                        (default: name). Paired-end sequencing data must be
                        sorted either by position or by read name, and the
                        sorting order must be specified. Ignored for single-
                        end data.
  --max-reads-in-buffer MAX_BUFFER_SIZE
                        When <alignment_file> is paired end sorted by
                        position, allow only so many reads to stay in memory
                        until the mates are found (raising this number will
                        use more memory). Has no effect for single end or
                        paired end sorted by name
  -s {yes,no,reverse}, --stranded {yes,no,reverse}
                        whether the data is from a strand-specific assay.
                        Specify 'yes', 'no', or 'reverse' (default: yes).
                        'reverse' means 'yes' with reversed strand
                        interpretation
  -a MINAQUAL, --minaqual MINAQUAL
                        skip all reads with alignment quality lower than the
                        given minimum value (default: 10)
  -t FEATURETYPE, --type FEATURETYPE
                        feature type (3rd column in GFF file) to be used, all
                        features of other type are ignored (default, suitable
                        for Ensembl GTF files: exon)
  -i IDATTR, --idattr IDATTR
                        GFF attribute to be used as feature ID (default,
                        suitable for Ensembl GTF files: gene_id)
  --additional-attr ADDITIONAL_ATTR
                        Additional feature attributes (default: none, suitable
                        for Ensembl GTF files: gene_name). Use multiple times
                        for each different attribute
  -m {union,intersection-strict,intersection-nonempty}, --mode {union,intersection-strict,intersection-nonempty}
                        mode to handle reads overlapping more than one feature
                        (choices: union, intersection-strict, intersection-
                        nonempty; default: union)
  --nonunique {none,all}
                        Whether to score reads that are not uniquely aligned
                        or ambiguously assigned to features
  --secondary-alignments {score,ignore}
                        Whether to score secondary alignments (0x100 flag)
  --supplementary-alignments {score,ignore}
                        Whether to score supplementary alignments (0x800 flag)
  -o SAMOUTS, --samout SAMOUTS
                        write out all SAM alignment records into SAM files
                        (one per input file needed), annotating each line with
                        its feature assignment (as an optional field with tag
                        'XF')
  -q, --quiet           suppress progress report
"""
        )
    )
    assert len(list(results)) == 15


def test_choice(parser):
    flag = elements.flag_with_arg.parseString("--format {sam,bam}")[0]
    assert flag.name == "--format"

    # Both sets should be the same
    assert len(flag.argtype.choices & {"sam", "bam"}) == 2


def test_noarg(parser):
    flag = parser.flag.parseString("-q, --quiet           suppress progress report")[0]
    assert flag.longest_synonym == "--quiet"
    assert len(flag.synonyms) == 2
    assert isinstance(flag.args, EmptyFlagArg)


@pytest.mark.skipif(
    not shutil.which("htseq-count"), reason="htseq-count is not installed"
)
def test_full(parser, local_executor):
    # Parse help
    help_text = local_executor.execute(["htseq-count", "--help"])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 2
    # There are two positional arguments
    assert len(flag_sections[0]) == 2
    # There are at least 15 flags
    assert len(flag_sections[1]) >= 15
