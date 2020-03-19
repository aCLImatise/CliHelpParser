from dataclasses import dataclass


@dataclass
class UsageElement:
    text: str
    optional: bool = False
    variable: bool = False
    flag: bool = False
