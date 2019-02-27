from pyparsing import Literal, Regex, indentedBlock, And, Word, alphanums, Or, OneOrMore, originalTextFor, SkipTo, \
    tokenMap, LineEnd, White, Optional, delimitedList, matchPreviousLiteral, nestedExpr
from dataclasses import dataclass
import re
import typing


def pick(*args):
    def action(s, loc, toks):
        if len(args) == 1:
            return toks[args[0]]
        else:
            return [toks[arg] for arg in args]

    return action


@dataclass
class Flag:
    flags: list
    description: str


@dataclass
class FlagName:
    name: str
    argtype: 'FlagArg'


@dataclass
class FlagArg:
    pass

@dataclass
class EmptyFlagArg(FlagArg):
    pass

@dataclass
class SimpleFlagArg(FlagArg):
    arg: str


@dataclass
class RepeatFlagArg(FlagArg):
    arg: str


@dataclass
class ChoiceFlagArg(FlagArg):
    choices: typing.List[str]


class CliParser:
    def __init__(self):
        stack = [1]

        self.short_flag = originalTextFor(Literal('-') + Word(alphanums, max=1))
        """A short flag has only a single dash and single character, e.g. `-m`"""
        self.long_flag = originalTextFor(Literal('--') + Word(alphanums))
        """A long flag has two dashes and any amount of characters, e.g. `--max-count`"""
        self.any_flag = self.short_flag ^ self.long_flag
        """The flag is the part with the dashes, e.g. `-m` or `--max-count`"""

        self.flag_arg_sep = Or([Literal('='), Literal(' ')]).leaveWhitespace()
        """The term that separates the flag from the arguments, e.g. in `--file=FILE` it's `=`"""

        self.arg_arg_sep = Or([Literal('='), Literal(' ')]).leaveWhitespace()
        """The term that separates arguments from each other, e.g. in `--file=FILE` it's `=`"""

        self.arg = Word(alphanums)
        """A single argument name, e.g. `FILE`"""

        self.list_type_arg = (
                self.arg
                + Literal(' ')
                + Literal('[')
                + matchPreviousLiteral(self.arg)
                + Literal('...')
                + Literal(']')
        )
        """When the argument is an array of values, e.g. when the help says `--samout SAMOUTS [SAMOUTS ...]`"""

        self.choice_type_arg = nestedExpr(
            opener='{',
            closer='}',
            content=delimitedList(Word(alphanums), delim=',')
        ).setParseAction(lambda s, loc, toks: ChoiceFlagArg(toks[0]))
        """When the argument is one from a list of values, e.g. when the help says `--format {sam,bam}`"""

        # self.arg_list = delimitedList(self.arg, delim=)
        self.arg_expression = (self.flag_arg_sep.suppress() + (
                self.list_type_arg ^ self.choice_type_arg ^ self.arg)).setParseAction(
            lambda s, loc, toks: toks[0]
            # 0/0
            # toks[1:]
        )
        """An argument with separator, e.g. `=FILE`"""

        self.flag_with_arg = (self.any_flag + Optional(self.arg_expression)).setParseAction(
            lambda s, loc, toks: (
                FlagName(name=toks[0], argtype=toks[1] if len(toks) > 0 else EmptyFlagArg())
            )
        )
        """e.g. `--max-count=NUM`"""

        self.flag_synonyms = delimitedList(self.flag_with_arg, delim=Literal(' ') ^ Literal(','))
        """
        When the help lists multiple synonyms for a flag, e.g:
        -n, --lines=NUM
        """

        # The description of the flag
        # e.g. for grep's `-o, --only-matching`, this is:
        # "Print only the matched (non-empty) parts of a matching line, with each such part on a separate output line."
        self.desc_line = originalTextFor(SkipTo(LineEnd()))
        self.indented_desc = indentedBlock(
            self.desc_line,
            indentStack=stack,
            indent=True
        ).setParseAction(
            lambda s, loc, toks: ' '.join([tok[0] for tok in toks[0]])
        )
        self.description = self.indented_desc  # Optional(one_line_desc) + Optional(self.indented_desc)
        # A self.description that takes up one line
        # one_line_desc = SkipTo(LineEnd())

        # A flag self.description that makes up an indented block
        # originalTextFor(SkipTo(flag_prefix ^ LineEnd()))

        # The entire flag documentation, including all synonyms and description
        self.flag = (
                self.flag_synonyms
                + self.description
        ).setParseAction(
            lambda s, loc, toks:
            (
                Flag(
                    flags=toks[0:-1],
                    description=toks[-1]
                )
            )
        )

        self.flags = indentedBlock(OneOrMore(self.flag), indentStack=stack, indent=True).setParseAction(
            lambda s, loc, toks: toks[0][0])
        self.flag_section_header = Regex('(arguments|options):', flags=re.IGNORECASE)
        self.flag_section = (self.flag_section_header + self.flags).setParseAction(lambda s, loc, toks: toks[1:])
