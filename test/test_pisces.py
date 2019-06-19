from test.util import get_help, parser
from declivity.parser import CliParser
from declivity.model import SimpleFlagArg
from pkg_resources import resource_filename


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


def test_pisces(parser):
    # Parse help
    with open(resource_filename(__name__, 'pisces.txt')) as fp:
        help_text = fp.read()

    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 5

    # There are two arguments in the first block
    assert len(flag_sections[0]) == 2

    # The very first argument has 3 synonyms
    assert len(flag_sections[0][0].synonyms) == 3
