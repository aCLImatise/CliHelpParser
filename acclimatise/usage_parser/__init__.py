# from acclimatise.flag_parser.elements import cli_id, any_flag, long_flag, short_flag, flag_with
from pathlib import Path

from acclimatise.flag_parser.elements import customIndentedBlock
from acclimatise.usage_parser.model import UsageElement

from .elements import *


def normalise_cline(tokens):
    """
    Normalise a command line string, such as ["dotnet", "Pisces.dll"], converting it to ["dotnet", "pisces"]
    :param tokens:
    :return:
    """
    return [Path(el.lower()).stem for el in tokens]


def parse_usage(cmd, text, debug=False):
    toks = usage.setDebug(debug).searchString(text)
    if not toks:
        # If we had no results, return an empty command
        return Command(command=cmd, positional=[], named=[])

    toks = toks[0]

    positional = [tok for tok in toks if isinstance(tok, UsageElement)]
    flags = [tok for tok in toks if isinstance(tok, Flag)]

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

    return Command(
        command=cmd,
        positional=[
            Positional(description="", position=i, name=el.text, optional=el.optional)
            for i, el in enumerate(positional)
        ],
        named=flags,
    )
