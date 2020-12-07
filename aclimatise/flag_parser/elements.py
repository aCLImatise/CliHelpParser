"""
Re-usable parser elements that aren't tied to the parser object
"""
from typing import List

from pyparsing import *

from aclimatise.model import *

#: Characters that delimit flag synonyms
synonym_delim_chars = ",|/"
#: Characters that can start a CLI element, e.g. "-@"
element_start_chars = alphanums + "@"
#: Characters that can be in the middle of a CLI element, e.g. "-some-arg"
element_body_chars = element_start_chars + "-_."
#: Characters that can only be used in arguments for flags e.g. "<file.fa|file.fa.gz>"
argument_body_chars = element_body_chars + "|"
#: Characters that can be in the middle of an argument that has brackets around it, e.g. "-arg <argument with space>"
delimited_body_chars = argument_body_chars + r" \/"

NL = OneOrMore(LineEnd().setWhitespaceChars("\t ").suppress()).setName("Newline")


cli_id = Word(initChars=element_start_chars, bodyChars=element_body_chars)

positional_name = Word(
    initChars=element_start_chars, bodyChars=element_body_chars, min=2
)

# short_flag = originalTextFor(Literal('-') + Word(alphanums + '@', max=1))
# """A short flag has only a single dash and single character, e.g. `-m`"""
# long_flag = originalTextFor(Literal('--') + cli_id)
# """A long flag has two dashes and any amount of characters, e.g. `--max-count`"""
any_flag = (
    originalTextFor("-" + Optional("-") + cli_id).leaveWhitespace().setName("Flag")
)
"""The flag is the part with the dashes, e.g. `-m` or `--max-count`"""

flag_arg_sep = (
    Or([Literal("="), Literal(" ")]).leaveWhitespace().setName("FlagArgSeparator")
)
"""The term that separates the flag from the arguments, e.g. in `--file=FILE` it's `=`"""

arg = Word(initChars=element_start_chars, bodyChars=argument_body_chars)
"""A single argument name, e.g. `FILE`"""

optional_args = Forward().setName("OptionalArg")


def visit_optional_args(s, lok, toks):
    if len(toks) == 1:
        return OptionalFlagArg(names=[toks[0]])
    else:
        first, _, sep, second, _ = toks
        if isinstance(second, str):
            return OptionalFlagArg(names=[first, second], separator=sep)
        elif isinstance(second, OptionalFlagArg):
            return OptionalFlagArg(names=[first] + second.names, separator=sep)


optional_args <<= (
    (arg + "[" + "," + (optional_args ^ arg) + "]")
    .setParseAction(visit_optional_args)
    .setName("OptionalArgs")
)
"""
When the flag has multiple arguments, some of which are optional, e.g.
-I FLOAT[,FLOAT[,INT[,INT]]]
"""

# simple_arg = arg.copy().setParseAction(
#     lambda s, loc, toks: SimpleFlagArg(toks[0]))
simple_arg = (
    (
        Or(
            [
                Word(initChars=element_start_chars, bodyChars=element_body_chars),
                # Allow spaces in the argument name, but only if it's enclosed in angle brackets
                (
                    Literal("<").suppress()
                    + Word(
                        initChars=element_start_chars, bodyChars=delimited_body_chars
                    )
                    + Literal(">").suppress()
                ).setName("angle_delimited_arg"),
            ]
        )
    )
    .leaveWhitespace()
    .setParseAction(lambda s, loc, toks: SimpleFlagArg(toks[0]))
).setName("SimpleArg")

repeated_segment = (
    (ZeroOrMore(arg) + Literal(".")[2, 3].suppress() + Optional(arg))
    .setParseAction(lambda s, loc, toks: RepeatFlagArg(toks[-1] or toks[0]))
    .setName("RepeatedSegment")
)  # Either ".." or "..."

list_type_arg = (
    (
        (arg + repeated_segment)
        ^ (arg + Literal("[").suppress() + repeated_segment + Literal("]").suppress())
    )
    .setParseAction(lambda s, loc, toks: toks[1])
    .setName("repeated_arg")
)
"""
    When the argument is an array of values, e.g. when the help says `--samout SAMOUTS [SAMOUTS ...]` or 
    `-i FILE1 FILE2 .. FILEn`

"""

choice_type_arg = (
    nestedExpr(opener="{", closer="}", content=delimitedList(cli_id, delim=","))
    .setParseAction(lambda s, loc, toks: ChoiceFlagArg(set(toks[0])))
    .setName("ChoiceArg")
)
"""When the argument is one from a list of values, e.g. when the help says `--format {sam,bam}`"""


def noop(s, loc, toks):
    return toks


arg_expression = (
    (
        flag_arg_sep.suppress()
        + (list_type_arg | choice_type_arg | optional_args | simple_arg)
    )
    # .leaveWhitespace()
    .setParseAction(lambda s, loc, toks: toks[0])
)
arg_expression.skipWhitespace = False
"""An argument with separator, e.g. `=FILE`"""

flag_with_arg = (
    (any_flag + Optional(arg_expression))
    .setParseAction(
        lambda s, loc, toks: (
            FlagSynonym(
                name=toks[0], argtype=toks[1] if len(toks) > 1 else EmptyFlagArg()
            )
        )
    )
    .setName("FlagWithArg")
)
flag_with_arg.skipWhitespace = True
"""e.g. `--max-count=NUM`"""

synonym_delim = (
    White() ^ (Optional(White()) + Char(synonym_delim_chars) + Optional(White()))
).leaveWhitespace()
"""
The character used to separate synonyms of a flag. Depending on the help text this might be a comma, pipe or space
"""

description_sep = White(min=1).suppress()
"""
The section that separates a flag from its description. This needs to be broad enough that it will match all different
formats of help outputs but not so broad that every single word starting with a dash will be matched as a flag
"""

# block_element_prefix = LineStart().leaveWhitespace()
block_element_prefix = (
    ((LineStart().leaveWhitespace() ^ Literal(":")) + White(min=1))
    .setName("block_element_prefix")
    .leaveWhitespace()
    .suppress()
)
"""
Each element (e.g. flag) in a list of flags must either start with a colon or nothing

e.g. in this example "index" is prefixed by a colon and "mem" is prefixed by a LineStart

Command: index         index sequences in the FASTA format
         mem           BWA-MEM algorithm
"""

flag_synonyms = delimitedList(flag_with_arg, delim=synonym_delim).setName(
    "FlagSynonyms"
)
"""
When the help lists multiple synonyms for a flag, e.g:
-n, --lines=NUM
"""


# The description of the flag
# e.g. for grep's `-o, --only-matching`, this is:
# "Print only the matched (non-empty) parts of a matching line, with each such part on a separate output line."
# desc_line = originalTextFor(SkipTo(LineEnd())).setName(
#     "DescriptionLine"
# )  # .setParseAction(success))
# desc_line = originalTextFor(
#     delimitedList(Regex("[^\s]+"), delim=" ", combine=True)
# ).leaveWhitespace()


def visit_description_line(s, loc, toks):
    return toks[0].strip()


description_line = (
    SkipTo(LineEnd(), include=True)
    .setParseAction(visit_description_line)
    .setWhitespaceChars(" \t")
).setName("DescriptionLine")
