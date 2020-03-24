import typing

from acclimatise.flag_parser.parser import CliParser
from acclimatise.usage_parser import parse_usage


def parse_help(cmd: typing.Collection[str], text: str, parse_positionals=True):
    help_command = CliParser(parse_positionals=parse_positionals).parse_command(
        name=cmd, cmd=text
    )
    usage_command = parse_usage(cmd, text)

    # Normally parsing the list of flags will provide a better command summary, but if it didn't give us anything,
    # fall back to the usage
    if len(help_command.positional) + len(help_command.named) == 0:
        command = usage_command
    else:
        command = help_command

        # However, even if we aren't referring to the usage for the whole command, we can cross-check to ensure we're
        # using some correct arguments
        if len(usage_command.positional) != len(help_command.positional):
            command.positional = usage_command.positional
        # confirmed = {pos.name for pos in usage_command.positional}
        # for positional in command.positional:
        #     if positional.name in confirmed:
        #         positional.usage_supported = True

        # Then, by default we filter out unsupported positionals, to remove false positives
        # if only_supported_positionals:
        #     command.positional = [pos for pos in command.positional if pos.usage_supported]

    return command
