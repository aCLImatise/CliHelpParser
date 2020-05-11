"""
Contains the objects that represent a "type" of data a flag argument might store
"""
import typing
from enum import Enum

from dataclasses import dataclass


@dataclass(unsafe_hash=True)
class CliType:
    """
    A data type used in the command-line
    """

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
    """
    One of a list of possible options
    """

    enum: Enum
    """
    The possible options as a Python Enum
    """


@dataclass(unsafe_hash=True)
class CliFloat(CliType):
    """
    Takes a floating-point value
    """

    pass


@dataclass(unsafe_hash=True)
class CliInteger(CliType):
    """
    Takes an integer value
    """

    _representable = {CliFloat}


@dataclass(unsafe_hash=True)
class CliString(CliType):
    """
    Takes a string value
    """

    pass


@dataclass(unsafe_hash=True)
class CliBoolean(CliType):
    """
    Takes a boolean value
    """

    pass


@dataclass(unsafe_hash=True)
class CliDir(CliType):
    """
    Takes a directory path
    """

    pass


@dataclass(unsafe_hash=True)
class CliFile(CliType):
    """
    Takes a file path
    """

    pass


@dataclass(unsafe_hash=True)
class CliDict(CliType):
    """
    Takes a dictionary value
    """

    key: CliType
    """
    Data type of the keys to this dictionary
    """

    value: CliType
    """
    Data type of the values to this dictionary
    """


@dataclass(unsafe_hash=True)
class CliList(CliType):
    """
    Takes a list value
    """

    value: CliType
    """
    Data type of the values in this list
    """


@dataclass(unsafe_hash=True)
class CliTuple(CliType):
    """
    Takes a list of values with a fixed length, possibly each with different types
    """

    values: typing.List[CliType]
    """
    List of types, in order, held within the tuple
    """

    @property
    def homogenous(self):
        """
        A tuple is homogenous if all types in the tuple are the same, aka the set of all types has length 1
        """
        return len(set([type(x) for x in self.values])) == 1
