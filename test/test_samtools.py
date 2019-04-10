from test.util import get_help, parser
from declivity.parser import CliParser


def test_samtools_index(parser):
    # Parse help
    help_text = get_help(['samtools', 'index'])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 1
    # There are two positional arguments
    assert len(flag_sections[0]) == 4


def test_singularity_style_flags(parser):
    flag = parser.flag.parseString( "    -n|--name   Specify a custom container name (first priority)" )[0]
    assert len(flag.synonyms) == 2
    assert flag.synonyms == ['-n', '--name']


def test_singularity_pull():
    parser = CliParser(parse_positionals=False)

    # Parse help
    help_text = get_help(['singularity', 'pull', '--help'])
    flag_sections = parser.flags.searchString(help_text)
    # There is one section for positional arguments and one for named arguments
    assert len(flag_sections) == 1
    # There are two positional arguments
    assert len(flag_sections[0]) == 5
