# from acclimatise.flag_parser.elements import cli_id, any_flag, long_flag, short_flag, flag_with
from acclimatise.usage_parser.model import UsageElement

from .elements import *


def parse_usage(cmd, text):
    toks = usage.searchString(text)
    if not toks:
        # If we had no results, return an empty command
        return Command(command=cmd, positional=[], named=[])

    toks = toks[0]

    positional = [tok for tok in toks if isinstance(tok, UsageElement)]
    flags = [tok for tok in toks if isinstance(tok, Flag)]

    # Remove an "options" argument which is just a proxy for other flags
    positional = [pos for pos in positional if pos.text != "options"]

    # The usage often starts with a re-iteration of the command name itself. Remove this if present
    truncate = 0
    for i, arg in enumerate(cmd):
        pos = positional[i]
        if arg == pos.text:
            truncate = i + 1
        else:
            break
    positional = positional[truncate:]

    if not any([tok for tok in positional if tok.variable]):
        # If the usage didn't explicitly mark anything as a variable using < > brackets, we have to assume that
        # everything other than flags are positional elements
        for element in positional:
            element.variable = True

    return Command(
        command=cmd,
        positional=[
            Positional(description="", position=i, name=el.text, optional=el.optional)
            for i, el in enumerate(positional)
        ],
        named=flags,
    )
