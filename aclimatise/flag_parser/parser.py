from itertools import groupby
from operator import attrgetter

import regex

from aclimatise.flag_parser.elements import *
from aclimatise.nlp import is_sentence
from aclimatise.parser import IndentCheckpoint, IndentParserMixin


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


# The reason we have a parser class here instead of just a function is so that we can store the parser state, in
# particular the indentation stack. Without this, we would have to use a global stack which would be even more
# worrying
class CliParser(IndentParserMixin):
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

    def __init__(self):
        super().__init__()

        def parse_description(s, lok, toks):
            text = "".join(toks)
            if len(text.strip()) == 0:
                return ""

            if all([non_alpha.match(word) for word in text.split()]):
                raise ParseException(
                    "This can't be a description block if all text is numeric!"
                )

            if len(multi_space.findall(text)) > len(single_space.findall(text)):
                raise ParseException(
                    "This description block has more unusual spaces than word spaces, it probably isn't a real description"
                )

            return text

        def visit_mandatory_description(s, loc, toks):
            text = toks[0].strip()
            if len(text.strip()) == 0:
                raise ParseException("A positional argument must have a description")

        self.mandatory_description = description_line.copy().setParseAction(
            visit_mandatory_description
        )

        self.flag = (
            (flag_synonyms + description_line)
            .setName("flag")
            .setParseAction(
                lambda s, loc, toks: (
                    Flag.from_synonyms(synonyms=toks[0:-1], description=toks[-1])
                )
            )
        )
        """
        The entire flag documentation, including all synonyms and one line of description
        """

        self.positional = (
            # Unlike with flags, we have to be a bit pickier about what defines a positional because it's very easy
            # for a paragraph of regular text to be parsed as a positional. So we add a minimum of 2 spaces separation
            (positional_name + White(min=2).suppress() + self.mandatory_description)
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

        self.block_element = self.flag | self.positional

        def visit_description_block(s, loc, toks):
            return "\n".join(toks)

        self.description_block = IndentCheckpoint(
            self.indent()
            + (self.peer_indent(allow_greater=True) + description_line)[1, ...]
            + self.dedent(precise=False),
            indent_stack=self.stack,
        ).setParseAction(visit_description_block)
        """
        The description block is the section of indented text after a flag. e.g. in this example:
            --use_strict (enforce strict mode)
                  type: bool  default: false
        The description block is "type: bool  default: false"
        """

        self.indented_flag = IndentCheckpoint(
            # We require that each flag is indented, but we don't check for a dedent: this allows the next flag to
            # have any indentation as long as it's more indented than the top level
            self.indent() + self.block_element,
            indent_stack=self.stack,
        )
        """
        Each flag can actually be at any indentation level, but we need to update the indent stack whenever we find one,
        so that we can identify the indented description block
        """

        def visit_flag_block(s, loc, toks):
            ret: List[CliArgument] = []

            # The tokens are a mix of flags and lines of text. Append the text to the previous flag
            for tok in toks:
                if isinstance(tok, CliArgument):
                    ret.append(tok)
                else:
                    # Add a newline if we already have some content
                    if len(ret[-1].description) > 0:
                        ret[-1].description += "\n"
                    ret[-1].description += tok

            ret = [flag for flag in ret if is_sentence(flag.description)]
            return ret

        self.flag_block = (
            IndentCheckpoint(
                self.indented_flag
                + (
                    # We pop the indent if parsing a new flag, since we no longer care about the previous flag
                    IndentCheckpoint(
                        self.pop_indent() + self.indented_flag, indent_stack=self.stack
                    )
                    # We don't pop the indent until after if parsing a description block, since we need to know
                    # that flag's indentation
                    | IndentCheckpoint(self.description_block, indent_stack=self.stack)
                )[...]
                + self.pop_indent(),
                indent_stack=self.stack,
            )
        ).setParseAction(visit_flag_block)
        """
        A block of flags is one or more flags, each followed by a description block. 
        The grammar is written this way so that parsing a flag is *always* prioritised over the description block, 
        preventing certain indented flags from being missed
        """

        self.colon_block = Literal(
            ":"
        ).suppress() + self.flag_block.copy().addParseAction(visit_colon_block)
        """
        When the block is introduced by a colon, we can be more lax about parsing
        """

        self.newline_block = (
            LineStart().leaveWhitespace()
            + White().suppress()
            + self.flag_block.copy().addParseAction(visit_flags)
        )
        """
        When the block is introduced by a newline, we have to be quite strict about its contents
        """

        self.unindented_flag_block = LineStart().suppress() + (
            self.flag + Optional(self.description_block)
        )[1, ...].setParseAction(visit_flag_block)
        # )  # delimitedList(self.flag, delim='\n')
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
            self.colon_block | self.newline_block | self.unindented_flag_block
        ).setName(
            "FlagList"
        )  # .leaveWhitespace()
        self.flags.skipWhitespace = False

        self.flag_section_header = Regex("(arguments|options):", flags=re.IGNORECASE)
        self.flag_section = (self.flag_section_header + self.flags).setParseAction(
            lambda s, loc, toks: toks[1:]
        )
