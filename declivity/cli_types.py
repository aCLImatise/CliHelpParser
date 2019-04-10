"""
Contains the objects that represent a "type" of data a flag argument might store
"""
from dataclasses import dataclass
import typing
from enum import Enum
import functools


@dataclass
class CliType:
    @property
    def representable(self) -> set:
        """
        Returns a set of types that this type could alternatively be represented as.
        Adds the class's own type to the _representable set
        """
        return self._representable.union({type(self)})

    # The list of types that this specific type could be representable as
    _representable = set()


@dataclass
class CliEnum(CliType):
    enum: Enum


@dataclass
class CliFloat(CliType):
    pass


@dataclass
class CliInteger(CliType):
    _representable = {CliFloat}


@dataclass
class CliString(CliType):
    pass


@dataclass
class CliBoolean(CliType):
    pass


@dataclass
class CliDir(CliType):
    pass


@dataclass
class CliFile(CliType):
    pass


@dataclass
class CliDict(CliType):
    key: CliType
    value: CliType


@dataclass
class CliList(CliType):
    value: CliType


@dataclass
class CliTuple(CliType):
    values: typing.List[CliType]

    @property
    def homogenous(self):
        # A tuple is homogenous if all types in the tuple are the same, aka the set of all types has length 1
        return len(set([type(x) for x in self.values])) == 1
