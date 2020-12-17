from dataclasses import dataclass
from io import StringIO
from os import PathLike
from pathlib import Path
from typing import Generator, List

from aclimatise.converter import WrapperGenerator
from aclimatise.model import Command
from aclimatise.yaml import yaml


@attr.s
class YmlGenerator(WrapperGenerator):
    """
    Internal YML format
    """

    @property
    def suffix(self) -> str:
        return ".yml"

    def save_to_file(self, cmd: Command, path: Path) -> None:
        with path.open("w") as fp:
            yaml.dump(cmd, fp)

    def save_to_string(self, cmd: Command) -> str:
        buffer = StringIO()
        yaml.dump(cmd, buffer)
        return buffer.getvalue()

    @classmethod
    def format(cls) -> str:
        return "yml"
