"""
Code relating to the command line interface to Declivity
"""
import argparse
import sys
from declivity.parser import CliParser
from declivity.converter import wdl, cwl, WrapperGenerator
import typing


def main():
    args = get_parser().parse_args()

    input = ''.join(sys.stdin.readlines())
    cmd = CliParser().parse_command(input, args.cmd.split())

    converter_cls: typing.Type[WrapperGenerator]
    if args.format == 'wdl':
        converter_cls = wdl.WdlGenerator
    elif args.format == 'cwl':
        converter_cls = cwl.CwlGenerator

    converter = converter_cls(
        generate_names=args.generate_names,
        ignore_positionals=args.no_pos
    )

    print(converter.generate_wrapper(cmd))


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'cmd',
        help='The base command this tool uses'
    )
    parser.add_argument(
        '-f',
        '--format',
        choices=['wdl', 'cwl'],
        required=True,
        help='The language in which to output the CLI wrapper'
    )
    parser.add_argument(
        '--no-pos',
        action='store_true',
        help=(
            "Don't include positional arguments, for example because the help formatting has some "
            "misleading sections that look like positional arguments"
        )
    )
    parser.add_argument(
        '-g',
        '--generate-names',
        action='store_true',
        help=(
            "Rather than using the long flag to generate the argument name, generate them automatically using the "
            "flag description. Generally helpful if there are no long flags, only short flags."
        )
    )
    return parser


if __name__ == '__main__':
    main()
