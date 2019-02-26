from pyparsing import Literal, Regex, indentedBlock, And, Word, alphanums, Or, OneOrMore, originalTextFor, SkipTo, tokenMap, LineEnd, White
from dataclasses import dataclass


@dataclass
class Flag:
    flag: str
    args: list
    description: str


short_flag = originalTextFor(Literal('-') + Word(alphanums, max=1))
long_flag = originalTextFor(Literal('--') + Word(alphanums))
any_flag = short_flag ^ long_flag

arg_sep = Or([Literal('='), Literal(' ')]).leaveWhitespace()
arg = Word(alphanums)
arg_expression = (arg_sep + arg).setParseAction(lambda s, loc, toks: toks[1])


# A description that takes up one line
one_line_desc = SkipTo(LineEnd())
# A flag description that makes up an indented block
stack = [0]
indented_desc = indentedBlock(Regex('.'), indentStack=stack, indent=True)
description = (one_line_desc + indented_desc) ^ one_line_desc ^ indented_desc
#originalTextFor(SkipTo(flag_prefix ^ LineEnd()))
flag = (any_flag + arg_expression + description).setParseAction(lambda s, loc, toks: Flag(
    flag=toks[0],
    args=toks[1],
    description=toks[2]
))

flags = indentedBlock(OneOrMore(flag), indentStack=stack, indent=True)
