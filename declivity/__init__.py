from declivity.parser import CliParser
from declivity.converter import wdl, cwl, WrapperGenerator, cases
import typing


def run_parser(
        text: str,
        cmd: str,
        format: str,
        no_pos: bool = False,
        generate_names: bool = False,
        case: str = 'snake'
) -> str:
    """
    Runs the parser over a help string
    :param text: The help output to parse
    :param cmd: The base command that was run
    :param format: The output format: wdl or cwl
    :param no_pos: If true, exclude conditionals
    :param generate_names: If true, use the flag description to generate argument names
    :param case: The case for variables. "snake" or "camel"
    """
    cmd = CliParser().parse_command(text, cmd.split())

    converter_cls: typing.Type[WrapperGenerator]
    if format == 'wdl':
        converter_cls = wdl.WdlGenerator
    elif format == 'cwl':
        converter_cls = cwl.CwlGenerator

    converter = converter_cls(
        generate_names=generate_names,
        ignore_positionals=no_pos,
        case=case
    )

    return converter.generate_wrapper(cmd)


__all__ = [
    run_parser,
    CliParser
]
