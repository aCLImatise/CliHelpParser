from pathlib import Path
from typing import List

from pyparsing import *

from aclimatise.flag_parser.elements import description_line
from aclimatise.parser import IndentCheckpoint, IndentParserMixin
from aclimatise.usage_parser.elements import usage_example
from aclimatise.usage_parser.model import UsageElement, UsageInstance

from .elements import *


def normalise_cline(tokens):
    """
    Normalise a command line string, such as ["dotnet", "Pisces.dll"], converting it to ["dotnet", "pisces"]
    :param tokens:
    :return:
    """
    return [Path(el.lower()).stem for el in tokens]


class UsageParser(IndentParserMixin):
    def __init__(self):
        super().__init__()

        def visit_description_block(s, loc, toks):
            return "\n".join(toks)

        self.description_block = IndentCheckpoint(
            self.indent()
            + (self.peer_indent(allow_greater=True) + description_line)[1, ...]
            + self.dedent(precise=False),
            indent_stack=self.stack,
        ).setParseAction(visit_description_block)

        def visit_single_usage(s, loc, toks):
            return [UsageInstance(items=list(toks), description=None)]

        self.single_usage = usage_example.copy().setParseAction(visit_single_usage)

        def visit_described_usage(s, loc, toks):
            if len(toks) > 0 and isinstance(toks[-1], str):
                description = toks[-1]
            else:
                description = None

            return UsageInstance(items=list(toks[:-1]), description=description)

        self.described_usage = (
            usage_example + Optional(self.description_block)
        ).setParseAction(visit_described_usage)

        def visit_multi_usage(s, loc, toks):
            return list(toks)

        self.multi_usage = (
            LineEnd().suppress()
            + (
                IndentCheckpoint(
                    # This indent ensures that every usage example is somewhat indented (more than column 1, at least),
                    # and also sets the baseline from which the description block is measured
                    self.indent() + self.described_usage
                    # The pop here doesn't check that we have dedented, but rather it just resets the indentation so that
                    # a new usage block can have a different indentation
                    + self.pop_indent(),
                    indent_stack=self.stack,
                )
            )[1, ...]
        ).setParseAction(visit_multi_usage)

        self.usage = (
            LineStart()
            + Regex("usage:", flags=re.IGNORECASE).suppress()
            + Optional(self.multi_usage | self.single_usage)
        ).setWhitespaceChars(
            "\t "
        )  # .setParseAction(visit_usage).setDebug()

    def parse_usage(self, cmd: List[str], usage: str, debug: bool = False) -> Command:
        # return self.usage.searchString(usage)
        usage_blocks = self.usage.setDebug(debug).searchString(usage)
        if not usage_blocks:
            # If we had no results, return an empty command
            return Command(command=cmd)

        instances = []
        all_positionals = []
        all_flags = []
        for block in usage_blocks:
            for instance in block:

                positional = [
                    tok for tok in instance.items if isinstance(tok, UsageElement)
                ]
                flags = [tok for tok in instance.items if isinstance(tok, Flag)]

                # Remove an "options" argument which is just a proxy for other flags
                # positional = [pos for pos in positional if pos.text.lower() != "options"]
                # The usage often starts with a re-iteration of the command name itself. Remove this if present
                for i in range(len(positional)):
                    # For each positional argument, if the entire cmd string is present, slice away this and everything before it
                    end = i + len(cmd)
                    if end <= len(positional) and normalise_cline(
                        [pos.text for pos in positional[i:end]]
                    ) == normalise_cline(cmd):
                        positional = positional[end:]

                if not any([tok for tok in positional if tok.variable]):
                    # If the usage didn't explicitly mark anything as a variable using < > brackets, we have to assume that
                    # everything other than flags are positional elements
                    for element in positional:
                        element.variable = True

                instances.append(instance)
                # Convert these UsageElements into Positionals
                all_positionals += [
                    Positional(
                        description="", position=i, name=el.text, optional=el.optional
                    )
                    for i, el in enumerate(positional)
                ]
                all_flags += flags

        return Command(
            command=cmd,
            positional=Positional.deduplicate(all_positionals),
            named=Flag.deduplicate(all_flags),
        )
