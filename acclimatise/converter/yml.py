from pathlib import Path
from typing import List

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
        return yaml.dump(cmd)

    def generate_tree(self, cmd: Command, out_dir: Path) -> Generator[Path, None, None]:
        for cmd in cmd.command_tree():
            path = (out_dir / cmd.as_filename).with_suffix(".yml")
            wrapper = self.generate_wrapper(cmd)
            path.write_text(wrapper, encoding="utf-8")
            yield path
