from io import StringIO
from os import PathLike
from pathlib import Path
from typing import Generator, List

from dataclasses import dataclass

from acclimatise.converter import WrapperGenerator
from acclimatise.model import Command
from acclimatise.yaml import yaml


@dataclass
class YmlGenerator(WrapperGenerator):
    """
    Internal YML format
    """

    @classmethod
    def format(cls) -> str:
        return "yml"

    def generate_wrapper(self, cmd: Command) -> str:
        buffer = StringIO()
        yaml.dump(cmd, buffer)
        return buffer.getvalue()

    def generate_tree(
        self, cmd: Command, out_dir: PathLike
    ) -> Generator[Path, None, None]:
        out_dir = Path(out_dir)
        for cmd in cmd.command_tree():
            path = (out_dir / cmd.as_filename).with_suffix(".yml")
            with path.open("w") as fp:
                yaml.dump(cmd, fp)
            yield path
