"""
Re-usable parser elements that aren't tied to the parser object
"""
from pyparsing import *
from pyparsing import _bslash

from acclimatise.model import *


def customIndentedBlock(
    blockStatementExpr, indentStack, indent=True, terminal=False, lax=False
):
    """
    Modified version of the indentedBlock construct provided by pyparsing. Allows fuzzier indent boundaries
    """
    backup_stack = indentStack[:]

    def reset_stack():
        indentStack[:] = backup_stack

    def checkPeerIndent(s, l, t):
        if l >= len(s):
            return
        curCol = col(l, s)

        # A terminal block doesn't have children, so we can assume that any sub-indent is a peer
        if terminal and curCol >= indentStack[-1]:
            return

        # If we're being lax, anything that's not a full dedent is a peer
        if lax and curCol > indentStack[-2]:
            return

        # Anything that is indented more than the previous indent level counts as a peer
        if curCol < indentStack[-1] or curCol <= indentStack[-2]:
            raise ParseException(s, l, "not a peer entry")

    def checkSubIndent(s, l, t):
        curCol = col(l, s)
        if curCol > indentStack[-1]:
            indentStack.append(curCol)
        else:
            raise ParseException(s, l, "not a subentry")

    def checkUnindent(s, l, t):
        if l >= len(s):
            indentStack.pop()
            return
        curCol = col(l, s)
        if not (indentStack and curCol < indentStack[-1]):
            raise ParseException(s, l, "not an unindent")
        indentStack.pop()

    NL = OneOrMore(LineEnd().setWhitespaceChars("\t ").suppress())
    INDENT = (Empty() + Empty().setParseAction(checkSubIndent)).setName("INDENT")
    PEER = Empty().setParseAction(checkPeerIndent).setName("")
    UNDENT = Empty().setParseAction(checkUnindent).setName("UNINDENT")
    if indent:
        smExpr = Group(
            Optional(NL)
            +
            # ~ FollowedBy(blockStatementExpr) +
            INDENT
            + (OneOrMore(PEER + Group(blockStatementExpr) + Optional(NL)))
            + UNDENT
        )
    else:
        smExpr = Group(
            Optional(NL) + (OneOrMore(PEER + Group(blockStatementExpr) + Optional(NL)))
        )
    smExpr.setFailAction(lambda a, b, c, d: reset_stack())
    blockStatementExpr.ignore(_bslash + LineEnd())
    return smExpr.setName("custom indented block")


cli_id = Word(initChars=alphas + "@", bodyChars=alphanums + "-_@")

# short_flag = originalTextFor(Literal('-') + Word(alphanums + '@', max=1))
# """A short flag has only a single dash and single character, e.g. `-m`"""
# long_flag = originalTextFor(Literal('--') + cli_id)
# """A long flag has two dashes and any amount of characters, e.g. `--max-count`"""
any_flag = originalTextFor("-" + Optional("-") + cli_id)
"""The flag is the part with the dashes, e.g. `-m` or `--max-count`"""

flag_arg_sep = Or([Literal("="), Literal(" ")]).leaveWhitespace()
"""The term that separates the flag from the arguments, e.g. in `--file=FILE` it's `=`"""

arg = cli_id.copy()
"""A single argument name, e.g. `FILE`"""

optional_args = Forward()


def visit_optional_args(s, lok, toks):
    if len(toks) == 1:
        return OptionalFlagArg(names=[toks[0]])
    else:
        other = toks[3]
        if isinstance(other, str):
            return OptionalFlagArg(names=[toks[0], other])
        elif isinstance(other, OptionalFlagArg):
            return OptionalFlagArg(names=[toks[0]] + other.names)


optional_args <<= (arg + "[" + "," + (optional_args ^ arg) + "]").setParseAction(
    visit_optional_args
)
"""
When the flag has multiple arguments, some of which are optional, e.g.
-I FLOAT[,FLOAT[,INT[,INT]]]
"""

# simple_arg = arg.copy().setParseAction(
#     lambda s, loc, toks: SimpleFlagArg(toks[0]))
simple_arg = Or(
    [
        Word(initChars=alphas, bodyChars=alphanums + "-_."),
        # Allow spaces in the argument name, but only if it's enclosed in angle brackets
        Literal("<").suppress()
        + Word(initChars=alphas, bodyChars=alphanums + "-_. ")
        + Literal(">").suppress(),
    ]
).setParseAction(lambda s, loc, toks: SimpleFlagArg(toks[0]))

list_type_arg = (
    arg
    + Literal(" ")
    + Literal("[")
    + matchPreviousLiteral(arg)
    + Optional(Literal(" "))
    + Literal("...")
    + Literal("]")
).setParseAction(lambda s, loc, toks: RepeatFlagArg(toks[0]))
"""When the argument is an array of values, e.g. when the help says `--samout SAMOUTS [SAMOUTS ...]`"""

choice_type_arg = nestedExpr(
    opener="{", closer="}", content=delimitedList(cli_id, delim=",")
).setParseAction(lambda s, loc, toks: ChoiceFlagArg(list(toks[0])))
"""When the argument is one from a list of values, e.g. when the help says `--format {sam,bam}`"""


def noop(s, loc, toks):
    return toks


arg_expression = (
    (
        flag_arg_sep.suppress()
        + (list_type_arg ^ choice_type_arg ^ optional_args ^ simple_arg)
    )
    .leaveWhitespace()
    .setParseAction(lambda s, loc, toks: toks[0])
)
"""An argument with separator, e.g. `=FILE`"""

flag_with_arg = (any_flag + Optional(arg_expression)).setParseAction(
    lambda s, loc, toks: (
        FlagSynonym(name=toks[0], argtype=toks[1] if len(toks) > 1 else EmptyFlagArg())
    )
)
"""e.g. `--max-count=NUM`"""

# TODO: this should be smarter, accepting ' ' or '| ' or '|' etc
synonym_delim = Word(" ,|", max=2).setParseAction(noop).leaveWhitespace()
"""
The character used to separate synonyms of a flag. Depending on the help text this might be a comma, pipe or space
"""

description_sep = White(min=1).setName("description_sep").suppress()
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

flag_synonyms = delimitedList(flag_with_arg, delim=synonym_delim)
"""
When the help lists multiple synonyms for a flag, e.g:
-n, --lines=NUM
"""


# The description of the flag
# e.g. for grep's `-o, --only-matching`, this is:
# "Print only the matched (non-empty) parts of a matching line, with each such part on a separate output line."
def success(a, b, c):
    pass


desc_line = originalTextFor(SkipTo(LineEnd()))  # .setParseAction(success))
