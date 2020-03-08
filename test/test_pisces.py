from test.util import get_help, parser
from declivity.parser import CliParser
from declivity.model import SimpleFlagArg
from pkg_resources import resource_filename
from textwrap import dedent
from .util import process_help_section as process


def test_pisces_flag(parser):
    cmd = """
  --targetlodfrequency, --targetvf <FLOAT>
    """
    flag_synonyms = parser.flag_synonyms.parseString(cmd)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_synonyms) == 2
    assert isinstance(flag_synonyms[1].argtype, SimpleFlagArg)
    assert flag_synonyms[1].argtype.name == '<FLOAT>'


def test_pisces_arg(parser):
    cmd = """
  --targetlodfrequency, --targetvf <FLOAT>
                     FLOAT Target Frequency to call a variant. Ie, to 
                       target a 5% allele frequency, we must call down 
                       to 2.6%, to capture that 5% allele 95% of the 
                       time. This parameter is used by the Somatic 
                       Genotyping Model
    """
    flag = parser.flag.parseString(cmd)[0]

    assert len(flag.synonyms) == 2
    assert flag.description.startswith('FLOAT Target Frequency')
    assert flag.args.name == '<FLOAT>'


def test_pisces_indent_dedent(parser):
    cmd = """
  -i, --intervalpaths <PATHS>
                             PATHS IntervalPath(s), single value or comma 
                               delimited list corresponding to BAMPath(s). At 
                               most one value should be provided if BAM folder 
                               is specified
      --coveragemethod <STRING>
                             STRING'approximate' or 'exact'. Exact is more 
                               precise but requires more memory (minimum 8 GB). 
                                Default approximate
      --baselogname <STRING> STRING 
  -d, --debug <BOOL>         BOOL
      --usestitchedxd <BOOL> BOOL Set to true to make use of the consensus 
                               read-direction information (the XD tag) from 
                               stitched reads. This is on by default when using 
                               Stitcher output bam, but must be deliberately 
                               set for Gemini output.
    """
    flags = parser.flags.parseString(cmd)

    assert len(flags) == 5


def test_pisces_multi_indent(parser):
    cmd = """
      --minvq, --minvariantqscore <INT>
                             INT MinimumVariantQScore to report variant
  -c, --mindp, --mindepth, --mincoverage <INT>
                             INT Minimum depth to call a variant
      --minvf, --minimumvariantfrequency, --minimumfrequency <FLOAT>
                             FLOAT MinimumFrequency to call a variant
      --targetlodfrequency, --targetvf <FLOAT>
                             FLOAT Target Frequency to call a variant. Ie, to 
                               target a 5% allele frequency, we must call down 
                               to 2.6%, to capture that 5% allele 95% of the 
                               time. This parameter is used by the Somatic 
                               Genotyping Model
      --vqfilter, --variantqualityfilter <INT>
   """
    flags = parser.flags.parseString(cmd)

    assert len(flags) == 5


def test_pisces(parser):
    # Parse help
    with open(resource_filename(__name__, 'pisces.txt')) as fp:
        help_text = fp.read()

    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 5

    # There are two arguments in the first block
    assert len(flag_sections[0]) == 2

    # There are 23 arguments in the second block
    assert len(flag_sections[1]) == 23

    # There are 4 arguments in the third block
    assert len(flag_sections[2]) == 4

    # There are 23 arguments in the fourth block
    assert len(flag_sections[3]) == 23

    # There are 6 arguments in the fifth block
    assert len(flag_sections[4]) == 6

    # The very first argument has 3 synonyms
    assert len(flag_sections[0][0].synonyms) == 3
