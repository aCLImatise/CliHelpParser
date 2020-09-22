import re

from pyparsing import *

# from aclimatise.flag_parser.elements import cli_id, any_flag, long_flag, short_flag, flag_with
from aclimatise.flag_parser.elements import (
    arg,
    argument_body_chars,
    delimited_body_chars,
    element_body_chars,
    element_start_chars,
    flag_with_arg,
    repeated_segment,
)
from aclimatise.model import (
    Command,
    EmptyFlagArg,
    Flag,
    FlagSynonym,
    Positional,
    SimpleFlagArg,
)
from aclimatise.usage_parser.model import UsageElement


def delimited_item(open, el, close):
    def action(s, loc, toks):
        return toks[1:-1]

    return (open + el + close).setParseAction(action)


usage_element = Forward()
element_char = arg.copy()  # Word(initChars=element_start_chars, bodyChars=)

mandatory_element = (
    element_char.copy()
    .setParseAction(
        lambda s, loc, toks: UsageElement(
            text=toks[0],
        )
    )
    .setName("MandatoryElement")
)
"""
A mandatory element in the command-line invocation. Might be a variable or a constant
"""

variable_element = (
    delimited_item(
        "<", Word(initChars=element_start_chars, bodyChars=delimited_body_chars), ">"
    )
    .setParseAction(lambda s, loc, toks: UsageElement(text=toks[1], variable=True))
    .setName("VariableElement")
)
"""
Any element inside angle brackets is a variable, meaning you are supposed to provide your own value for it.
However, some usage formats show variables without the angle brackets
"""


def visit_optional_section(s, loc, toks):
    inner = toks[1:-1]
    for tok in inner:
        tok.optional = True
    return inner


optional_section = (
    delimited_item("[", OneOrMore(usage_element), "]")
    .setParseAction(visit_optional_section)
    .setName("OptionalSection")
)
"""
Anything can be nested within square brackets, which indicates that everything there is optional
"""

# flag_arg = Or([
#     variable_element,
#     element_char
# ])
"""
The argument after a flag, e.g. in "-b <bamlist.fofn>" this would be everything after "-b"
"""

# short_flag_name = Char(alphas)
"""
The single character for a short flag, e.g. "n" for a "-n" flag
"""

# short_flag = (
#         '-' + short_flag_name + White() + Optional(flag_arg)
# ).setParseAction(
#     lambda s, loc, toks:
#     Flag.from_synonyms([FlagSynonym(
#         name=toks[0] + toks[1],
#         argtype=SimpleFlagArg(toks[3]) if toks[3] else EmptyFlagArg()
#     )], description=None)
# )
"""
The usage can contain a flag with its argument
"""

# long_flag = (
#         '--' + element_char + White() + Optional(flag_arg)
# ).setParseAction(lambda s, loc, toks: Flag.from_synonyms([FlagSynonym(
#     name=toks[1],
#     argtype=SimpleFlagArg(toks[3]) if toks[3] else EmptyFlagArg()
# )]))
"""
The usage can contain a flag with its argument
"""


def visit_short_flag_list(s, loc, toks):
    return [
        Flag.from_synonyms(
            [FlagSynonym(name="-" + flag, argtype=EmptyFlagArg())], description=None
        )
        for flag in toks[1:]
    ]


# short_flag_list = ('-' + short_flag_name + OneOrMore(short_flag_name)).setParseAction(
#     visit_short_flag_list).leaveWhitespace()
"""
Used to illustrate where a list of short flags could be used, e.g. -nurlf indicates -n or -u etc
"""


def visit_list_element(s, loc, toks):
    # Pick the last element if there is one, otherwise use the first element
    # This gives us a better name like 'inN.bam' instead of 'in2.bam'
    els = [tok for tok in toks if isinstance(tok, (UsageElement, Flag))]
    for el in els:
        el.repeatable = True
    return els[-1]


options_placeholder = (
    Regex("options?", flags=re.IGNORECASE).suppress().setName("OptionsPlaceholder")
)

list_element = (
    (
        OneOrMore(options_placeholder ^ mandatory_element ^ variable_element)
        + Literal(".")[2, 3]
        + Optional(options_placeholder ^ mandatory_element ^ variable_element)
    )
    .setParseAction(visit_list_element)
    .setName("list_element")
)
"""
When one or more arguments are allowed, e.g. "<in2.bam> ... <inN.bam>"
"""

usage_flag = (
    And([flag_with_arg])
    .setParseAction(lambda s, loc, toks: Flag.from_synonyms(toks, description=""))
    .setName("usage_flag")
)


usage_element <<= Or(
    [
        optional_section,
        list_element,
        # short_flag_list,
        usage_flag,
        variable_element,
        options_placeholder,
        mandatory_element,
    ]
).setName("usage_element")

stack = [1]


def visit_usage(s, loc, toks):
    # Fix up stack inconsistencies
    while len(stack) > 1:
        stack.pop()

    return toks[0][0]


usage_example = OneOrMore(usage_element, stopOn=LineEnd())
"""
Each usage example is a single line of text, e.g. 

  shell [options] -e string
"""

usage = (
    LineStart()
    + Regex("usage:", flags=re.IGNORECASE).suppress()
    + OneOrMore(usage_example)
)  # .setParseAction(visit_usage).setDebug()
"""
Each usage block can have one or more lines of different usage. e.g.

Usage:
  shell [options] -e string
    execute string in V8
  shell [options] file1 file2 ... filek
    run JavaScript scripts in file1, file2, ..., filek
"""


# usage = Regex('usage:', flags=re.IGNORECASE).suppress() + delimitedList(usage_element, delim=Or([' ', '\n']))
# indentedBlock(
#     delimitedList(usage_element, delim=' '),
#     indentStack=stack,
#     indent=True
# )
