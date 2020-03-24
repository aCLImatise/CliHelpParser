"""
Contains the objects that represent a "type" of data a flag argument might store
"""
import functools
import typing
from dataclasses import dataclass
from enum import Enum


@dataclass(unsafe_hash=True)
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


@dataclass(unsafe_hash=True)
class CliEnum(CliType):
    enum: Enum


@dataclass(unsafe_hash=True)
class CliFloat(CliType):
    pass


@dataclass(unsafe_hash=True)
class CliInteger(CliType):
    _representable = {CliFloat}


@dataclass(unsafe_hash=True)
class CliString(CliType):
    pass


@dataclass(unsafe_hash=True)
class CliBoolean(CliType):
    pass


@dataclass(unsafe_hash=True)
class CliDir(CliType):
    pass


@dataclass(unsafe_hash=True)
class CliFile(CliType):
    pass


@dataclass(unsafe_hash=True)
class CliDict(CliType):
    key: CliType
    value: CliType


@dataclass(unsafe_hash=True)
class CliList(CliType):
    value: CliType


@dataclass(unsafe_hash=True)
class CliTuple(CliType):
    values: typing.List[CliType]

    @property
    def homogenous(self):
        # A tuple is homogenous if all types in the tuple are the same, aka the set of all types has length 1
        return len(set([type(x) for x in self.values])) == 1
