import subprocess
import typing

from acclimatise.flag_parser.parser import CliParser
from acclimatise.model import Command
from acclimatise.usage_parser import parse_usage
from pyparsing import ParseBaseException


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


def best_cmd(
    cmd: typing.List[str],
    flags: typing.Iterable[str] = ([], ["-h"], ["--help"], ["--usage"]),
) -> Command:
    """
    Determine the best Command instance for a given command line tool, by trying many
    different help flags, such as --help and -h
    :param cmd: The command to analyse, e.g. ['wc'] or ['bwa', 'mem']
    :param flags: A list of help flags to try, e.g. ['--help', '-h']
    """
    # For each help flag, run the command and then try to parse it
    commands = []
    for flag in flags:
        help_cmd = cmd + flag
        try:
            final = execute_cmd(help_cmd)
            commands.append(parse_help(cmd, final))
        except (ParseBaseException, UnicodeDecodeError):
            # If parsing fails, this wasn't the right flag to use
            continue

    return max(commands, key=lambda com: len(com.named) + len(com.positional))


def execute_cmd(help_cmd: typing.List[str]) -> str:
    """
    Execute a command defined by a list of arguments, and return the result as a string
    """
    try:
        proc = subprocess.run(
            help_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1
        )
        return (proc.stdout or proc.stderr).decode("utf_8")
    except subprocess.TimeoutExpired:
        return ""
