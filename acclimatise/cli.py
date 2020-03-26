"""
Code relating to the command line interface to acclimatise
"""
import argparse
import subprocess
import sys
import typing

from acclimatise.converter import WrapperGenerator, cases
from acclimatise.model import Command
from acclimatise.parser import parse_help
from pyparsing import ParseBaseException


def main():
    args = get_parser().parse_args()

    # Allow input of help text either by running the command, or using stdin
    if args.stdin:
        stdin = "".join(sys.stdin.readlines())
        command = parse_help(args.cmd, stdin)
    else:
        command = best_cmd(args.cmd)

    converter_cls = WrapperGenerator.choose_converter(args.format)
    converter = converter_cls(
        generate_names=args.generate_names,
        ignore_positionals=args.no_pos,
        case=args.case,
    )
    output = converter.generate_wrapper(command)
    print(output)


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
        final = execute_cmd(help_cmd)
        try:
            commands.append(parse_help(cmd, final))
        except ParseBaseException:
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


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", nargs="+", help="The base command this tool uses")
    parser.add_argument(
        "-f",
        "--format",
        choices=["wdl", "cwl"],
        required=True,
        help="The language in which to output the CLI wrapper",
    )
    parser.add_argument(
        "--no-pos",
        action="store_true",
        help=(
            "Don't include positional arguments, for example because the help formatting has some "
            "misleading sections that look like positional arguments"
        ),
    )
    parser.add_argument(
        "-g",
        "--generate-names",
        action="store_true",
        help=(
            "Rather than using the long flag to generate the argument name, generate them automatically using the "
            "flag description. Generally helpful if there are no long flags, only short flags."
        ),
    )
    parser.add_argument(
        "-c",
        "--case",
        choices=cases,
        help=(
            "Which case to use for variable names. If not set, defaults to the language defaults: snake_case for CWL"
            " and snake_case for WDL"
        ),
        default="snake",
    )
    parser.add_argument(
        "--stdin",
        help="Accept the help text from stdin instead of running the command",
        action="store_true",
    )
    return parser


if __name__ == "__main__":
    main()
