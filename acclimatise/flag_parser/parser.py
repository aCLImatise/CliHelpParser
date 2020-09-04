from itertools import groupby
from operator import attrgetter

import regex

from acclimatise.flag_parser.elements import *


class IndentCheckpoint(ParserElement):
    def __init__(self, expr: ParserElement, indent_stack: List[int]):
        super().__init__()
        self.expr = expr
        self.stack = indent_stack

    def parseImpl(self, instring, loc, doActions=True):
        # Backup the stack whenever we reach this element during the parse
        backup_stack = self.stack[:]
        try:
            return self.expr._parse(instring, loc, doActions, callPreParse=False)
        except ParseException as e:
            # On a parse failure, reset the stack
            self.stack[:] = backup_stack
            raise e

    def __str__(self):
        if hasattr(self, "name"):
            return self.name

        if self.strRepr is None:
            self.strRepr = "Indented[" + str(self.expr) + "]"

        return self.strRepr


def pick(*args):
    def action(s, loc, toks):
        if len(args) == 1:
            return toks[args[0]]
        else:
            return [toks[arg] for arg in args]

    return action


def unique_by(
    iterable: typing.Iterable,
    by: typing.Callable[[typing.Any], typing.Hashable],
    keep: str = "first",
) -> typing.List:
    """
    Removes duplicates from an iterable, by grouping by the result of the ``by`` argument, and then
    :param iterable: An iterable to make unique
    :param by: A function that returns a value for each element in ``iterable``
    :param keep: Either "first", "last", or "none". "none" means "delete all objects that are duplicates"
    """
    groups = groupby(iterable, by)
    ret = []
    for name, group in groups:
        group = list(group)
        if keep == "first":
            ret.append(group[0])
        elif keep == "last":
            ret.append(group[-1])
        elif keep == "none":
            if len(group) == 1:
                ret.append(group[0])
    return ret


#: Used to find normal word boundaries
single_space = regex.compile(r"\b \b")

#: Used to find unusual word boundaries
multi_space = regex.compile(r"\b[\s]{2,}\b")

# Used to find words that contain no alphabetical characters
non_alpha = regex.compile(r"^[^[:alpha:]]+$")


class CliParser:
    def parse_command(self, cmd, name) -> Command:
        all_flags = list(itertools.chain.from_iterable(self.flags.searchString(cmd)))
        # If flags aren't unique, they likely aren't real flags
        named = unique_by(
            [flag for flag in all_flags if isinstance(flag, Flag)],
            by=attrgetter("longest_synonym"),
            keep="none",
        )
        positional = unique_by(
            [flag for flag in all_flags if isinstance(flag, Positional)],
            by=attrgetter("name"),
            keep="none",
        )
        return Command(command=name, positional=positional, named=named)

    def __init__(self, parse_positionals=True):
        self.stack = [0]

        def parse_description(s, lok, toks):
            text = " ".join([tok[0] for tok in toks[0]])
            if all([non_alpha.match(word) for word in text.split()]):
                raise ParseException(
                    "This can't be a description block if all text is numeric!"
                )
            if len(multi_space.findall(text)) > len(single_space.findall(text)):
                raise ParseException(
                    "This description block has more unusual spaces than word spaces, it probably isn't a real description"
                )

            return text

        # self.indented_desc = (
        #     customIndentedBlock(
        #         desc_line, indentStack=stack, indent=True, terminal=True
        #     )
        #     .setParseAction(parse_description)
        #     .setName("DescriptionBlock")
        # )

        # self.description = self.indented_desc.copy().setName(
        #     "description"
        # )  # Optional(one_line_desc) + Optional(indented_desc)
        self.description = SkipTo(LineEnd(), include=True).setParseAction(
            lambda s, loc, toks: toks[0]
        )
        # A description that takes up one line
        # one_line_desc = SkipTo(LineEnd())

        # A flag description that makes up an indented block
        # originalTextFor(SkipTo(flag_prefix ^ LineEnd()))

        # The entire flag documentation, including all synonyms and description
        self.flag = (
            (flag_synonyms + self.description)
            .setName("flag")
            .setParseAction(
                lambda s, loc, toks: (
                    Flag.from_synonyms(synonyms=toks[0:-1], description=toks[-1])
                )
            )
        )

        self.positional = (
            # Unlike with flags, we have to be a bit pickier about what defines a positional because it's very easy
            # for a paragraph of regular text to be parsed as a positional. So we add a minimum of 2 spaces separation
            (cli_id + White(min=2).suppress() + self.description)
            .setName("positional")
            .setParseAction(
                lambda s, loc, toks: Positional(
                    name=toks[0], description=toks[1], position=-1
                )
            )
        )
        """
        A positional argument, e.g. a required argument that doesn't use dashes
        """

        def visit_flags(s, loc, toks):
            # Give the correct position to the positional arguments
            processed = []
            counter = 0
            # flags = toks[0]

            for flag in toks:
                if isinstance(flag, Positional):
                    flag.position = counter
                    counter += 1
                processed.append(flag)

            return processed

        def visit_colon_block(s, loc, toks):
            toks = visit_flags(s, loc, toks)
            if len(toks) < 2:
                raise ParseException(
                    "If the block starts with a colon it must match two or more tokens",
                    loc=loc,
                )
            else:
                return toks

        block_element = self.flag | self.positional

        # self.flag_block = customIndentedBlock(
        #     block_element, indentStack=stack, indent=True, lax=True
        # ).setName("FlagBlock")
        # A flag block is one flag, followed by other flags, or more description lines. These description lines will
        # get concatenated onto the previous flag.
        # self.indent = (Empty() + Empty().setParseAction(self.check_sub_indent)).setName('Indent')
        # self.peer = Empty().setParseAction(self.check_peer_indent).setName('Peer')
        # self.unindent = Empty().setParseAction(self.check_unindent).setName('Unindent')

        def visit_flag_block(s, loc, toks):
            ret: List[Flag] = []

            # The tokens are a mix of flags and lines of text. Append the text to the previous flag
            for tok in toks:
                if isinstance(tok, Flag):
                    ret.append(tok)
                else:
                    ret[-1].description += "\n" + tok
            return ret

        self.flag_block = IndentCheckpoint(
            (self.peer_indent() | self.indent())
            + block_element
            + (
                block_element
                | IndentCheckpoint(
                    self.indent()
                    + (self.peer_indent(allow_greater=True) + self.description)[...]
                    + self.dedent(),
                    indent_stack=self.stack,
                )
            )[...]
            + self.dedent(),
            indent_stack=self.stack,
        ).setParseAction(
            visit_flag_block
        )  # self.flag_block.skipWhitespace = True

        self.colon_block = Literal(
            ":"
        ).suppress() + self.flag_block.copy().setParseAction(visit_colon_block)

        self.newline_block = (
            LineStart().leaveWhitespace()
            + White().suppress()
            + self.flag_block.copy().setParseAction(visit_flags)
        )

        self.unindented_flag_block = LineStart().suppress() + OneOrMore(
            self.flag
        )  # delimitedList(self.flag, delim='\n')
        # self.unindented_flag_block.leaveWhitespace()
        self.unindented_flag_block.skipWhitespace = False
        """
        This is a list of flags that aren't indented. Because of this, we don't parse positional elements here, because
        doing so would include basically any paragraph of text
        """

        # self.colon_block.skipWhitespace = True
        # self.newline_block.skipWhitespace = True

        # A flag block can start with a colon, but then it must have 2 or more flags. If it starts with a newline it
        # only has to have one flag at least
        self.flags = (
            self.colon_block | self.newline_block  # ^ self.unindented_flag_block
        ).setName(
            "FlagList"
        )  # .leaveWhitespace()
        self.flags.skipWhitespace = False

        self.flag_section_header = Regex("(arguments|options):", flags=re.IGNORECASE)
        self.flag_section = (self.flag_section_header + self.flags).setParseAction(
            lambda s, loc, toks: toks[1:]
        )

    def peer_indent(self, allow_greater=False):
        """
        :param allow_greater: Allow greater indent than the previous indentation, but don't add it to the stack
        """

        def check_peer_indent(s, l, t):
            if l >= len(s):
                return
            curCol = col(l, s)
            if allow_greater and curCol >= self.stack[-1]:
                return
            elif curCol == self.stack[-1]:
                return
            else:
                if curCol > self.stack[-1]:
                    raise ParseException(s, l, "illegal nesting")
                raise ParseException(s, l, "not a peer entry")

        return Empty().setParseAction(check_peer_indent).setName("Peer")

    def indent(self):
        def check_sub_indent(s, l, t):
            curCol = col(l, s)
            if curCol > self.stack[-1]:
                self.stack.append(curCol)
            else:
                raise ParseException(s, l, "not a subentry")

        return (Empty() + Empty().setParseAction(check_sub_indent)).setName("Indent")

    def dedent(self):
        def check_dedent(s, l, t):
            if l >= len(s):
                return
            curCol = col(l, s)
            if not (self.stack and curCol in self.stack):
                raise ParseException(s, l, "not an unindent")
            if curCol < self.stack[-1]:
                self.stack.pop()

        return Empty().setParseAction(check_dedent).setName("Unindent")
