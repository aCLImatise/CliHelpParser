import logging
import pty
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

logger = logging.getLogger("acclimatise")


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
    fields = {"help_text": text}
    for field in dataclasses.fields(Command):
        fields[field.name] = (
            fields.get(field.name)
            or getattr(help_command, field.name)
            or getattr(usage_command, field.name)
        )

    return Command(**fields)


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
    logger.info("Trying flags for {}".format(" ".join(cmd)))
    commands = []
    for flag in flags:
        help_cmd = cmd + flag
        logger.info("Trying {}".format(" ".join(help_cmd)))
        try:
            final = execute_cmd(help_cmd, **run_kwargs)
            result = parse_help(cmd, final)
            result.generated_using = flag
            commands.append(result)
        except (ParseBaseException, UnicodeDecodeError) as e:
            # If parsing fails, this wasn't the right flag to use
            continue

    # Sort by flags primarily, and if they're equal, return the command with the longest help text
    best = max(
        commands,
        key=lambda com: (
            len(com.named) + len(com.positional),
            len(com.help_text) if com.help_text else 0,
        ),
    )
    logger.info("The best help flag seems to be {}".format(" ".join(best.command)))
    return best


def is_subcommand(command: Command, parent: Command) -> bool:
    """
    Returns true if command is a valid subcommand, relative to its parent
    """
    # Recursively call this on all ancestors
    if parent.parent is not None and not is_subcommand(command, parent.parent):
        return False

    # This isn't a subcommand if it has the same input text as the parent
    if command.help_text and command.help_text == parent.help_text:
        return False

    # This isn't a subcommand if it has no flags
    if len(command.positional) + len(command.named) == 0:
        return False

    # This isn't a subcommand if it shares any positional with the parent command
    for pos_a, pos_b in zip(parent.positional, command.positional):
        if pos_a == pos_b:
            return False

    # This isn't a subcommand if it shares any flags with the parent command
    for flag_a, flag_b in zip(parent.named, command.named):
        if flag_a == flag_b:
            return False

    return True


def explore_command(
    cmd: typing.List[str],
    flags: typing.Iterable[str] = ([], ["-h"], ["--help"], ["--usage"]),
    parent: typing.Optional[Command] = None,
    run_kwargs: dict = {},
    max_depth: int = 3,
    try_subcommand_flags=False,
) -> typing.Optional[Command]:
    """
    Given a command to start with, builds a model of this command and all its subcommands (if they exist).
    Use this if you know the command you want to parse, you don't know which flags it responds to with help text, and
    you want to include subcommands.

    :param cmd: Command line executable and arguments to explore
    :param flags: List of flags to append to cmd in order to look for help commands, e.g. "--help"
    :param parent: A parent Command to add this command to as a subcommand, if this command actually exists
    :param run_kwargs: kwargs to pass into subprocess.run, when we run the executable
    :param try_subcommand_flags: If true, try all the ``flags`` on each subcommand. If False, the default, we choose
    the best help flag on the parent command and then use that same one on each child
    """
    logger.info("Exploring {}".format(" ".join(cmd)))
    command = best_cmd(cmd, flags, run_kwargs=run_kwargs)

    # Check if this is a valid subcommand
    if parent:
        if is_subcommand(command, parent):
            logger.info("{} seems to be a valid subcommand".format(" ".join(cmd)))
            command.parent = parent
        else:
            logger.info(
                "{} does not seem to be a valid subcommand".format(" ".join(cmd))
            )
            return None

    # Recursively call this function on positionals, but only do this if we aren't at max depth
    if command.depth < max_depth:
        # By default we use the best parent help-flag
        child_flags = flags if try_subcommand_flags else [command.generated_using]
        for positional in command.positional:
            subcommand = explore_command(
                cmd=cmd + [positional.name],
                flags=child_flags,
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
    master, slave = pty.openpty()
    defaults = dict(
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, stdin=slave
    )
    defaults.update(kwargs)
    try:
        proc = subprocess.run(help_cmd, **defaults)
        return (proc.stdout or proc.stderr).decode("utf_8")
    except subprocess.TimeoutExpired:
        return ""
