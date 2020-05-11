import subprocess
import typing

import dataclasses
from pyparsing import ParseBaseException

from acclimatise.converter import WrapperGenerator
from acclimatise.converter.cwl import CwlGenerator
from acclimatise.converter.wdl import WdlGenerator
from acclimatise.converter.yml import YmlGenerator
from acclimatise.flag_parser.parser import CliParser
from acclimatise.model import Command
from acclimatise.usage_parser import parse_usage


def parse_help(
    cmd: typing.Collection[str], text: str, parse_positionals=True
) -> Command:
    """
    Parse a string of help text into a Command. Use this if you already have run the executable and extracted the
    help text yourself

    :param cmd: List of arguments used to generate this help text, e.g. ['bwa', 'mem']
    :param text: The help text to parse
    :param parse_positionals: If false, don't parse positional arguments
    """
    help_command = CliParser(parse_positionals=parse_positionals).parse_command(
        name=cmd, cmd=text
    )
    usage_command = parse_usage(cmd, text)

    # Combine the two commands by picking from the help_command where possible, otherwise falling back on the usage
    fields = {}
    for field in dataclasses.fields(Command):
        fields[field.name] = getattr(help_command, field.name) or getattr(
            usage_command, field.name
        )
    command = Command(**fields)

    # Normally parsing the list of flags will provide a better command summary, but if it didn't give us anything,
    # fall back to the usage
    # if len(help_command.positional) + len(help_command.named) == 0:
    #     command = usage_command
    # else:
    #     command = help_command

    # However, even if we aren't referring to the usage for the whole command, we can cross-check to ensure we're
    # using some correct arguments
    # if len(usage_command.positional) != len(help_command.positional):
    #     command.positional = usage_command.positional
    # confirmed = {pos.name for pos in usage_command.positional}
    # for positional in command.positional:
    #     if positional.name in confirmed:
    #         positional.usage_supported = True

    # Then, by default we filter out unsupported positionals, to remove false positives
    # if only_supported_positionals:
    #     command.positional = [pos for pos in command.positional if pos.usage_supported]

    return command


def best_cmd(
    cmd: typing.List[str],
    flags: typing.Iterable[str] = ([], ["-h"], ["--help"], ["--usage"]),
    run_kwargs: dict = {},
) -> Command:
    """
    Determine the best Command instance for a given command line tool, by trying many
    different help flags, such as --help and -h, then return the Command. Use this if you know the command you want to
    parse, but you don't know which flags it responds to with help text. Unlike :py:func:`aclimatise.explore_command`,
    this doesn't even attempt to parse subcommands.

    :param cmd: The command to analyse, e.g. ['wc'] or ['bwa', 'mem']
    :param flags: A list of help flags to try, e.g. ['--help', '-h']
    :param run_kwargs: kwargs to pass into subprocess.run, when we run the executable
    """
    # For each help flag, run the command and then try to parse it
    commands = []
    for flag in flags:
        help_cmd = cmd + flag
        try:
            final = execute_cmd(help_cmd, **run_kwargs)
            commands.append(parse_help(cmd, final))
        except (ParseBaseException, UnicodeDecodeError):
            # If parsing fails, this wasn't the right flag to use
            continue

    return max(commands, key=lambda com: len(com.named) + len(com.positional))


def explore_command(
    cmd: typing.List[str],
    flags: typing.Iterable[str] = ([], ["-h"], ["--help"], ["--usage"]),
    parent: typing.Optional[Command] = None,
    run_kwargs: dict = {},
) -> typing.Optional[Command]:
    """
    Given a command to start with, builds a model of this command and all its subcommands (if they exist).
    Use this if you know the command you want to parse, you don't know which flags it responds to with help text, and
    you want to include subcommands.

    :param cmd: Command line executable and arguments to explore
    :param flags: List of flags to append to cmd in order to look for help commands, e.g. "--help"
    :param parent: A parent Command to add this command to as a subcommand, if this command actually exists
    :param run_kwargs: kwargs to pass into subprocess.run, when we run the executable
    """
    command = best_cmd(cmd, flags, run_kwargs=run_kwargs)

    if parent:
        # This isn't a subcommand if it has no flags
        if len(command.positional) + len(command.named) == 0:
            return None

        # This isn't a subcommand if it shares any positional with the parent command
        for pos_a, pos_b in zip(parent.positional, command.positional):
            if pos_a == pos_b:
                return None

        # This isn't a subcommand if it shares any flags with the parent command
        for flag_a, flag_b in zip(parent.named, command.named):
            if flag_a == flag_b:
                return None

    # Recursively call this function on positionals
    for positional in command.positional:
        subcommand = explore_command(
            cmd=cmd + [positional.name],
            flags=flags,
            parent=command,
            run_kwargs=run_kwargs,
        )
        if subcommand is not None:
            command.subcommands.append(subcommand)

            # If we had any subcommands then we probably don't have any positionals, or at least don't care about them
            command.positional = []

    return command


def execute_cmd(help_cmd: typing.List[str], **kwargs) -> str:
    """
    Execute a command defined by a list of arguments, and return the result as a string
    """
    defaults = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    defaults.update(kwargs)
    try:
        proc = subprocess.run(help_cmd, **defaults)
        return (proc.stdout or proc.stderr).decode("utf_8")
    except subprocess.TimeoutExpired:
        return ""
