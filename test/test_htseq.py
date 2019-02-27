"""
Uses htseq-count, which is used as an example of a Python argparse CLI
"""
from test.util import get_help, parser
from textwrap import dedent


def test_short(parser):
    flag = parser.short_flag.parseString(dedent(
        """
        -i IDATTR
        """
    ))
    print(flag)


def test_long_short(parser):
    flag = parser.flag.parseString(dedent(
        """
        -i IDATTR, --idattr IDATTR
                          GFF attribute to be used as feature ID (default,
                          suitable for Ensembl GTF files: gene_id)
        """
    ))[0]
    print(flag)

def test_choice(parser):
    flag = parser.flag_with_arg.parseString('--format {sam,bam}')[0]
    assert flag.name == '--format'
    assert list(flag.argtype.choices) == ['sam', 'bam']


def test_full(parser):
    # Parse help
    help_text = get_help(['htseq-count', '--help'])
    results = list(parser.flag.scanString(help_text))

    assert len(results) == 3

    for tokens, start, end in results:
        assert len(tokens) > 0
