import typing

import attr

from aclimatise.flag_parser.parser import CliParser
from aclimatise.model import Command, Flag
from aclimatise.usage_parser.parser import UsageParser


def parse_help(cmd: typing.Collection[str], text: str, max_length=1000) -> Command:
    """
    Parse a string of help text into a Command. Use this if you already have run the executable and extracted the
    help text yourself

    :param cmd: List of arguments used to generate this help text, e.g. ['bwa', 'mem']
    :param text: The help text to parse
    :param max_length: If the input text has more than this many lines, no attempt will be made to parse the file (as
        it's too large, will likely take a long time, and there's probably an underlying problem if this has happened).
        In this case, an empty Command will be returned
    """
    if len(text.splitlines()) > max_length:
        return Command(list(cmd))

    help_command = CliParser().parse_command(name=cmd, cmd=text)
    usage_command = UsageParser().parse_usage(list(cmd), text)

    # Combine the two commands by picking from the help_command where possible, otherwise falling back on the usage
    fields = dict(
        help_text=text,
        # Use the help command's positionals preferentially, but fall back to usage
        positional=help_command.positional or usage_command.positional,
        # Combine the flags from both help and usage
        named=list(Flag.combine([help_command.named, usage_command.named])),
    )
    for field in attr.fields(Command):
        fields[field.name] = (
            fields.get(field.name)
            or getattr(help_command, field.name)
            or getattr(usage_command, field.name)
        )

    return Command(**fields)
