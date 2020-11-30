"""
Code relating to the command line interface to aCLImatise
"""
import sys
from pathlib import Path
from typing import Iterable, Tuple

import click

from aclimatise import WrapperGenerator, explore_command, parse_help
from aclimatise.execution.local import LocalExecutor
from aclimatise.execution.man import ManPageExecutor
from aclimatise.flag_parser.parser import CliParser

# Some common options
opt_generate_names = click.option(
    "--generate-names",
    "-g",
    is_flag=True,
    help=(
        "Rather than using the long flag to generate the argument name, generate them automatically using the "
        "flag description. Generally helpful if there are no long flags, only short flags."
    ),
)
opt_case = click.option(
    "--case",
    "-c",
    type=click.Choice(WrapperGenerator.cases),
    help=(
        "Which case to use for variable names. If not set, defaults to the language defaults: snake_case for CWL"
        " and snake_case for WDL"
    ),
    default="snake",
)
opt_cmd = click.argument("cmd", nargs=-1, required=True)


@click.group()
def main():
    pass


@main.command(help="Run an executable and explore all subcommands")
@opt_cmd
@opt_case
@opt_generate_names
@click.option(
    "--man",
    "-m",
    is_flag=True,
    help="Parse the help using its man page, rather than by executing the command. This will fail if the man page doesn't exist",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=1,
    help="How many levels of subcommands we should look for. Depth 2 means commands can be 3 levels deep, such as "
    "``git submodule foreach``",
)
@click.option(
    "--format",
    "-f",
    "formats",
    type=click.Choice(["wdl", "cwl", "yml"]),
    multiple=True,
    default=("yml", "wdl", "cwl"),
    help="The language in which to output the CLI wrapper",
)
@click.option(
    "--out-dir",
    "-o",
    type=Path,
    help="Directory in which to put the output files",
    default=Path(),
)
@click.option(
    "--help-flag",
    "-l",
    type=str,
    help="Flag to append to the end of the command to make it output help text",
)
@click.option(
    "--subcommands/--no-subcommands", default=True, help="Look for subcommands"
)
def explore(
    cmd: Iterable[str],
    out_dir: Path,
    formats: Tuple[str],
    subcommands: bool,
    case: str,
    generate_names: bool,
    man: bool,
    help_flag: str,
    depth: int = None,
):
    # We only support these two executors via CLI because the docker executor would require some additional config
    if man:
        exec = ManPageExecutor()
    else:
        kwargs = {}
        if help_flag is not None:
            kwargs["flags"] = [[help_flag]]
        exec = LocalExecutor(**kwargs)

    if subcommands:
        command = exec.explore(list(cmd), max_depth=depth)
    else:
        command = exec.convert(list(cmd))

    for format in formats:
        converter_cls = WrapperGenerator.choose_converter(format)
        converter = converter_cls(
            generate_names=generate_names,
            case=case,
        )
        list(converter.generate_tree(command, out_dir))


@main.command(
    help="Read a command help from stdin and output a tool definition to stdout"
)
@opt_cmd
@opt_generate_names
@opt_case
@click.option(
    "--format",
    "-f",
    type=click.Choice(["wdl", "cwl", "yml"]),
    default="cwl",
    help="The language in which to output the CLI wrapper",
)
def pipe(cmd, generate_names, case, format):
    stdin = "".join(sys.stdin.readlines())
    command = parse_help(cmd, stdin)

    converter_cls = WrapperGenerator.choose_converter(format)
    converter = converter_cls(
        generate_names=generate_names,
        case=case,
    )
    output = converter.save_to_string(command)
    print(output)


@main.command(help="Output a representation of the internal grammar")
def railroad():
    try:
        from pyparsing.diagram import to_railroad, railroad_to_html

        parser = CliParser()
        railroad = to_railroad(parser.flags)
        sys.stdout.write(railroad_to_html(railroad))
    except ImportError:
        print(
            "You need PyParsing 3.0.0a2 or greater to use this feature", file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
