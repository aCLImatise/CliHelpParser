from textwrap import dedent


def process_help_section(help):
    """
    Does some preprocessing on a help text segment to facilitate testing
    """
    help = help.strip("\n")
    return dedent(help)
