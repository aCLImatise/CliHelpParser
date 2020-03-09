from pyparsing import Literal, Regex, indentedBlock, And, Word, alphanums, Or, OneOrMore, originalTextFor, SkipTo, \
    tokenMap, LineEnd, White, Optional, delimitedList, matchPreviousLiteral, nestedExpr, alphas, Forward, LineStart, \
    Group, col, Empty, _bslash, ParseException
import re
from declivity.model import Command, Flag, EmptyFlagArg, OptionalFlagArg, SimpleFlagArg, RepeatFlagArg, _FlagSynonym, \
    ChoiceFlagArg, Positional
import itertools


def pick(*args):
    def action(s, loc, toks):
        if len(args) == 1:
            return toks[args[0]]
        else:
            return [toks[arg] for arg in args]

    return action


def customIndentedBlock(blockStatementExpr, indentStack, indent=True, terminal=False, lax=False):
    """
    Modified version of the indentedBlock construct provided by pyparsing. Allows fuzzier indent boundaries
    """
    backup_stack = indentStack[:]

    def reset_stack():
        indentStack[:] = backup_stack

    def checkPeerIndent(s, l, t):
        if l >= len(s): return
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
        if l >= len(s): return
        curCol = col(l, s)
        if not (indentStack and curCol < indentStack[-1]):
            raise ParseException(s, l, "not an unindent")
        indentStack.pop()

    NL = OneOrMore(LineEnd().setWhitespaceChars("\t ").suppress())
    INDENT = (Empty() + Empty().setParseAction(checkSubIndent)).setName('INDENT')
    PEER = Empty().setParseAction(checkPeerIndent).setName('')
    UNDENT = Empty().setParseAction(checkUnindent).setName('UNINDENT')
    if indent:
        smExpr = Group(Optional(NL) +
                       # ~ FollowedBy(blockStatementExpr) +
                       INDENT + (OneOrMore(PEER + Group(blockStatementExpr) + Optional(NL))) + UNDENT)
    else:
        smExpr = Group(Optional(NL) +
                       (OneOrMore(PEER + Group(blockStatementExpr) + Optional(NL))))
    smExpr.setFailAction(lambda a, b, c, d: reset_stack())
    blockStatementExpr.ignore(_bslash + LineEnd())
    return smExpr.setName('custom indented block')


class CliParser:
    def parse_command(self, cmd, name):
        all_flags = list(itertools.chain.from_iterable(self.flags.searchString(cmd)))
        named = [flag for flag in all_flags if isinstance(flag, Flag)]
        positional = [flag for flag in all_flags if isinstance(flag, Positional)]
        return Command(
            command=name,
            positional=positional,
            named=named
        )

    def __init__(self, parse_positionals=True):
        stack = [1]
        self.cli_id = Word(initChars=alphas + '<>', bodyChars=alphanums + '-_<>')

        self.short_flag = originalTextFor(Literal('-') + Word(alphanums + '@', max=1))
        """A short flag has only a single dash and single character, e.g. `-m`"""
        self.long_flag = originalTextFor(Literal('--') + self.cli_id)
        """A long flag has two dashes and any amount of characters, e.g. `--max-count`"""
        self.any_flag = self.short_flag ^ self.long_flag
        """The flag is the part with the dashes, e.g. `-m` or `--max-count`"""

        self.flag_arg_sep = Or([Literal('='), Literal(' ')]).leaveWhitespace()
        """The term that separates the flag from the arguments, e.g. in `--file=FILE` it's `=`"""

        self.arg = self.cli_id.copy()
        """A single argument name, e.g. `FILE`"""

        def visit_optional_args(s, lok, toks):
            if len(toks) == 1:
                return OptionalFlagArg(names=[toks[0]])
            else:
                other = toks[3]
                if isinstance(other, str):
                    return OptionalFlagArg(names=[toks[0], other])
                elif isinstance(other, OptionalFlagArg):
                    return OptionalFlagArg(names=[toks[0]] + other.names)

        self.optional_args = Forward()
        self.optional_args <<= (
                self.arg
                + Literal('[') + Literal(',') + (self.optional_args ^ self.arg) + Literal(']')
        ).setParseAction(visit_optional_args)
        """
        When the flag has multiple arguments, some of which are optional, e.g.
        -I FLOAT[,FLOAT[,INT[,INT]]]
        """

        self.simple_arg = self.arg.copy().setParseAction(lambda s, loc, toks: SimpleFlagArg(toks[0]))

        self.list_type_arg = (
                self.arg
                + Literal(' ')
                + Literal('[')
                + matchPreviousLiteral(self.arg)
                + Optional(Literal(' '))
                + Literal('...')
                + Literal(']')
        ).setParseAction(lambda s, loc, toks: RepeatFlagArg(toks[0]))
        """When the argument is an array of values, e.g. when the help says `--samout SAMOUTS [SAMOUTS ...]`"""

        self.choice_type_arg = nestedExpr(
            opener='{',
            closer='}',
            content=delimitedList(self.cli_id, delim=',')
        ).setParseAction(lambda s, loc, toks: ChoiceFlagArg(list(toks[0])))
        """When the argument is one from a list of values, e.g. when the help says `--format {sam,bam}`"""

        def noop(s, loc, toks):
            return toks

        self.arg_expression = (
                self.flag_arg_sep.suppress() + (
                self.list_type_arg ^ self.choice_type_arg ^ self.optional_args ^ self.simple_arg)
        ).leaveWhitespace().setParseAction(
            lambda s, loc, toks: toks[0]
        )
        """An argument with separator, e.g. `=FILE`"""

        self.flag_with_arg = (self.any_flag + Optional(self.arg_expression)).setParseAction(
            lambda s, loc, toks: (
                _FlagSynonym(name=toks[0], argtype=toks[1] if len(toks) > 1 else EmptyFlagArg())
            )
        )
        """e.g. `--max-count=NUM`"""

        # TODO: this should be smarter, accepting ' ' or '| ' or '|' etc
        self.synonym_delim = Word(' ,|', max=2).setParseAction(noop)
        """
        The character used to separate synonyms of a flag. Depending on the help text this might be a comma, pipe or space
        """

        self.flag_synonyms = delimitedList(self.flag_with_arg, delim=self.synonym_delim)
        """
        When the help lists multiple synonyms for a flag, e.g:
        -n, --lines=NUM
        """

        # The description of the flag
        # e.g. for grep's `-o, --only-matching`, this is:
        # "Print only the matched (non-empty) parts of a matching line, with each such part on a separate output line."
        def success(a, b, c):
            pass

        self.desc_line = originalTextFor(SkipTo(LineEnd()))  # .setParseAction(success))
        self.indented_desc = customIndentedBlock(
            self.desc_line,
            indentStack=stack,
            indent=True,
            terminal=True
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
                Flag.from_synonyms(synonyms=toks[0:-1], description=toks[-1])
            )
        )

        self.positional = (self.cli_id + self.description).setParseAction(lambda s, loc, toks: Positional(
            name=toks[0],
            description=toks[1],
            position=-1
        ))
        """
        A positional argument, e.g. a required argument that doesn't use dashes
        """

        def visit_flags(s, loc, toks):
            # Give the correct position to the positional arguments
            processed = []
            counter = 0
            flags = toks[0]

            for flag, in flags:
                if isinstance(flag, Positional):
                    flag.position = counter
                    counter += 1
                processed.append(flag)

            return processed

        if parse_positionals:
            self.flags = LineStart().leaveWhitespace() + customIndentedBlock(
                self.flag ^ self.positional,
                indentStack=stack,
                indent=True,
                lax=True
            ).setParseAction(visit_flags)
        else:
            self.flags = LineStart().leaveWhitespace() + customIndentedBlock(
                self.flag,
                indentStack=stack,
                indent=True,
                lax=True
            ).setParseAction(visit_flags)
        self.flag_section_header = Regex('(arguments|options):', flags=re.IGNORECASE)
        self.flag_section = (self.flag_section_header + self.flags).setParseAction(lambda s, loc, toks: toks[1:])
