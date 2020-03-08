"""
Code relating to the command line interface to Declivity
"""
import argparse
import sys
from declivity import run_parser
from declivity.parser import CliParser
from declivity.converter import wdl, cwl, WrapperGenerator, cases
import typing


def main():
    args = get_parser().parse_args()
    input = ''.join(sys.stdin.readlines())
    print(run_parser(text=input, **vars(args)))


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
    parser.add_argument(
        '-c',
        '--case',
        choices=cases,
        help=(
            "Which case to use for variable names. If not set, defaults to the language defaults: snake_case for CWL"
            " and snake_case for WDL"
        ),
        default='snake'
    )
    return parser


if __name__ == '__main__':
    main()
