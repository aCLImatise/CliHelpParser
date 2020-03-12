from pyparsing import *

mandatoryElement = ""

usageElement = Or(
    mandatoryElement,

)

"""
"partial" element that still needs a stack to be instantiated
"""
return Regex('usage:', flags=re.IGNORECASE) + customIndentedBlock(
    OneOrMore(usageElement),
    indentStack=stack,
    indent=True
)

