"""
Contains the objects that represent a "type" of data a flag argument might store
"""
import typing
from enum import Enum

import attr

from aclimatise.yaml import AttrYamlMixin


@attr.s(auto_attribs=True, frozen=True)
class CliType(AttrYamlMixin):
    """
    A data type used in the command-line
    """

    @staticmethod
    def lowest_common_type(types: typing.Iterable["CliType"]) -> "CliType":
        type_set: typing.Set[typing.Type[CliType]] = {type(t) for t in types}

        if len(type_set) == 1:
            # If there is only one type, use it
            return next(iter(types))

        if len(type_set) == 2 and CliInteger in type_set and CliFloat in type_set:
            # If they're all numeric, they can be represented as floats
            return CliFloat()

        if {
            CliDir,
            CliDict,
            CliFile,
            CliTuple,
            CliList,
        } & type_set:
            # These complex types cannot be represented in a simpler way
            raise Exception(
                "There is no common type between {}".format(
                    ", ".join([str(typ) for typ in type_set])
                )
            )

        else:
            # Most of the time, strings can be used to represent primitive types
            return CliString()

    @property
    def representable(self) -> set:
        """
        Returns a set of types that this type could alternatively be represented as.
        Adds the class's own type to the _representable set
        """
        return self._representable.union({type(self)})

    # The list of types that this specific type could be representable as
    _representable = set()


@attr.s(auto_attribs=True, frozen=True)
class CliEnum(CliType):
    """
    One of a list of possible options
    """

    enum: Enum
    """
    The possible options as a Python Enum
    """


@attr.s(auto_attribs=True, frozen=True)
class CliFloat(CliType):
    """
    Takes a floating-point value
    """

    pass


@attr.s(auto_attribs=True, frozen=True)
class CliInteger(CliType):
    """
    Takes an integer value
    """

    _representable = {CliFloat}


@attr.s(auto_attribs=True, frozen=True)
class CliString(CliType):
    """
    Takes a string value
    """

    pass


@attr.s(auto_attribs=True, frozen=True)
class CliBoolean(CliType):
    """
    Takes a boolean value
    """

    pass


@attr.s(auto_attribs=True, frozen=True)
class CliFileSystemType(CliType):
    """
    Takes a directory / file path
    """

    output: bool = False
    """
    Indicator if it is input or output
    """


@attr.s(auto_attribs=True, frozen=True)
class CliDir(CliFileSystemType):
    """
    Takes a directory path
    """

    pass


@attr.s(auto_attribs=True, frozen=True)
class CliFile(CliFileSystemType):
    """
    Takes a file path
    """

    pass


@attr.s(auto_attribs=True, frozen=True)
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


@attr.s(auto_attribs=True, frozen=True)
class CliList(CliType):
    """
    Takes a list value
    """

    value: CliType
    """
    Data type of the values in this list
    """


@attr.s(auto_attribs=True, frozen=True)
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
