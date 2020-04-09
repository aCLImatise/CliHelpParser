from acclimatise.flag_parser.elements import *


def pick(*args):
    def action(s, loc, toks):
        if len(args) == 1:
            return toks[args[0]]
        else:
            return [toks[arg] for arg in args]

    return action


class CliParser:
    def parse_command(self, cmd, name) -> Command:
        all_flags = list(itertools.chain.from_iterable(self.flags.searchString(cmd)))
        named = [flag for flag in all_flags if isinstance(flag, Flag)]
        positional = [flag for flag in all_flags if isinstance(flag, Positional)]
        return Command(command=name, positional=positional, named=named)

    def __init__(self, parse_positionals=True):
        stack = [1]

        self.indented_desc = customIndentedBlock(
            desc_line, indentStack=stack, indent=True, terminal=True
        ).setParseAction(lambda s, loc, toks: " ".join([tok[0] for tok in toks[0]]))

        self.description = self.indented_desc.copy().setName(
            "description"
        )  # Optional(one_line_desc) + Optional(indented_desc)
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
            flags = toks[0]

            for (flag,) in flags:
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

        if parse_positionals:
            block_element = self.flag ^ self.positional
        else:
            block_element = self.flag

        self.flag_block = customIndentedBlock(
            block_element, indentStack=stack, indent=True, lax=True
        ).setName("flag_block")

        # self.flag_block.skipWhitespace = True

        self.colon_block = Literal(
            ":"
        ).suppress() + self.flag_block.copy().setParseAction(visit_colon_block)

        self.newline_block = (
            LineStart().leaveWhitespace()
            + White().suppress()
            + self.flag_block.copy().setParseAction(visit_flags)
        )

        # self.colon_block.skipWhitespace = True
        # self.newline_block.skipWhitespace = True

        # A flag block can start with a colon, but then it must have 2 or more flags. If it starts with a newline it
        # only has to have one flag at least
        self.flags = self.newline_block ^ self.colon_block  # .leaveWhitespace()
        self.flags.skipWhitespace = False

        self.flag_section_header = Regex("(arguments|options):", flags=re.IGNORECASE)
        self.flag_section = (self.flag_section_header + self.flags).setParseAction(
            lambda s, loc, toks: toks[1:]
        )
