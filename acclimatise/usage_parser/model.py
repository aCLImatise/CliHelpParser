from dataclasses import dataclass


@dataclass
class UsageElement:
    text: str
    """
    The name of this element, as defined in the usage section
    """

    optional: bool = False
    """
    Whether or not this element is required
    """

    variable: bool = False
    """
    True if this is a variable, ie you are supposed to replace this text with your own, False if this is a constant
    that you shouldn't change, e.g. the name of the application
    """

    # flag: bool = False
    """
    True if this is a flag (starts with dashes) and not a regular element
    """

    repeatable: bool = False
    """
    If this flag/argument can be used multiple times
    """
