from pyparsing import *
# from acclimatise.flag_parser.elements import cli_id, any_flag, long_flag, short_flag
from acclimatise.usage_parser.model import UsageElement

def delimited_item(open, el, close):
    def action(s, loc, toks):
        return toks[1]

    return (open + el + close).setParseAction(action)

usage_element = Forward()
element_char = Word(initChars=alphanums, bodyChars=alphanums + '_-')

mandatory_element = element_char.copy().setParseAction(lambda s, loc, toks: UsageElement(
    text=toks[0],
))
"""
A mandatory element in the command-line invocation. Might be a variable or a constant
"""

variable_element = delimited_item("<", element_char, ">")
"""
Any element inside angle brackets is a variable, meaning you are supposed to provide your own value for it.
However, some usage formats show variables without the angle brackets
"""

optional_section = delimited_item("[", usage_element, "]")
"""
Anything can be nested within square brackets, which indicates that everything there is optional
"""

flag_arg = Or([
    variable_element,
    mandatory_element
])
"""
The argument after a flag, e.g. in "-b <bamlist.fofn>" this would be everything after "-b"
"""

short_flag_name = Char(alphas)
"""
The single character for a short flag, e.g. "n" for a "-n" flag
"""

short_flag = '-' + short_flag_name + " " + Optional(flag_arg)
"""
The usage can contain a flag with its argument
"""

long_flag = '--' + element_char + " " + Optional(flag_arg)
"""
The usage can contain a flag with its argument
"""

short_flag_list = '-' + OneOrMore(short_flag_name)
"""
Used to illustrate where a list of short flags could be used, e.g. -nurlf indicates -n or -u etc
"""

list_element = Or([
    mandatory_element,
    variable_element
]) + '...' + Optional(Or([
    mandatory_element,
    variable_element
]))
"""
When one or more arguments are allowed, e.g. "<in2.bam> ... <inN.bam>"
"""

usage_element <<= Or([
    optional_section,
    list_element,
    short_flag_list,
    short_flag,
    long_flag,
    variable_element,
    mandatory_element,
])

stack = [0]
usage = Regex('usage:', flags=re.IGNORECASE) + OneOrMore(usage_element)
# indentedBlock(
#     delimitedList(usage_element, delim=' '),
#     indentStack=stack,
#     indent=True
# )

