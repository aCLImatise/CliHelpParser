import argparse
import sys
from declivity.parser import CliParser
from declivity.converter import wdl


def main():
    args = get_parser().parse_args()

    if args.output_format == 'wdl':
        input = ''.join(sys.stdin.readlines())
        cmd = CliParser().parse_command(input, ['bwa', 'mem'])
        print(wdl.make_tasks(cmd))


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_format', choices=['wdl'])
    return parser


if __name__ == '__main__':
    main()
