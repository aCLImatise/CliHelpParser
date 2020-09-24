from io import StringIO
from os import PathLike
from pathlib import Path
from typing import Generator, List

from dataclasses import dataclass
from ruamel.yaml.representer import RoundTripRepresenter

from aclimatise.converter import WrapperGenerator
from aclimatise.model import Command
from aclimatise.yaml import YAML
from aclimatise.yaml import yaml as verbose_yaml

concise_yml = YAML()

# We need all data from the decorators on the data model
concise_yml.representer = RoundTripRepresenter()
concise_yml.representer.yaml_representers = (
    verbose_yaml.representer.yaml_representers.copy()
)


@dataclass
class YmlGenerator(WrapperGenerator):
    """
    Internal YML format
    """

    # If true, we dump the parent and child Commands, otherwise we don't
    dump_associations: bool = True

    def __post_init__(self):
        if self.dump_associations:
            self.yaml = verbose_yaml
        else:
            self.yaml = concise_yml

    @staticmethod
    def represent(dumper, data: Command):
        node = dumper.represent_yaml_object("!Command", data, Command)

        # Transform certain keys
        def transform(field):
            key, value = field
            if key.value == "subcommands":
                return key, dumper.represent_list([])
            elif key.value == "parent":
                return key, dumper.represent_none(None)
            return field

        node.value = [transform(field) for field in node.value]
        return node

    @property
    def suffix(self) -> str:
        return ".yml"

    def save_to_file(self, cmd: Command, path: Path) -> None:
        with path.open("w") as fp:
            self.yaml.dump(cmd, fp)

    def save_to_string(self, cmd: Command) -> str:
        buffer = StringIO()
        self.yaml.dump(cmd, buffer)
        return buffer.getvalue()

    @classmethod
    def format(cls) -> str:
        return "yml"


# We process the Command so that we don't dump subcommands or parent commands
concise_yml.representer.add_representer(Command, YmlGenerator.represent)
