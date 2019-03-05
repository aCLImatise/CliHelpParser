from dataclasses import dataclass
import typing


@dataclass
class CliType:
    pass


@dataclass
class CliInteger(CliType):
    pass


@dataclass
class CliFloat(CliType):
    pass


@dataclass
class CliString(CliType):
    pass


@dataclass
class CliBoolean(CliType):
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