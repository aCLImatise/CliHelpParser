import inspect
import tempfile
from io import IOBase, StringIO, TextIOBase
from os import PathLike
from pathlib import Path
from typing import Generator, List

from dataclasses import dataclass

from acclimatise import cli_types
from acclimatise.converter import NamedArgument, WrapperGenerator
from acclimatise.model import CliArgument, Command, Flag, Positional
from acclimatise.yaml import yaml


@dataclass
class GalaxyGenerator(WrapperGenerator):
    case = "snake"

    @classmethod
    def format(cls) -> str:
        return "galaxy"

    @property
    def suffix(self) -> str:
        return ".xml"

    def save_to_string(self, cmd: Command) -> str:
        # Todo
        pass

    def save_to_file(self, cmd: Command, path: Path) -> None:
        # Todo
        pass

    @classmethod
    def validate(cls, wrapper: str, cmd: Command = None, explore=True):
        pass
