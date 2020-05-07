import inspect
import tempfile
from io import IOBase, StringIO, TextIOBase
from pathlib import Path
from typing import Generator

from cwl_utils.parser_v1_1 import (
    CommandInputParameter,
    CommandLineBinding,
    CommandLineTool,
)
from dataclasses import dataclass

from acclimatise import cli_types
from acclimatise.converter import WrapperGenerator
from acclimatise.model import Command
from acclimatise.yaml import yaml


def with_default_none(func, *args, **kwargs):
    """
    Calls a function, and inserts None for all arguments you didn't provide
    """
    spec = inspect.getfullargspec(func)
    defaults = {arg: None for arg in spec.args}
    defaults.pop("self", None)
    return func(*args, **{**defaults, **kwargs})


@dataclass
class CwlGenerator(WrapperGenerator):
    case = "snake"

    @classmethod
    def format(cls) -> str:
        return "cwl"

    @staticmethod
    def snake_case(words: list):
        return "_".join([word.lower() for word in words])

    @staticmethod
    def to_cwl_type(typ: cli_types.CliType):
        if isinstance(typ, cli_types.CliFile):
            return "File"
        elif isinstance(typ, cli_types.CliDir):
            return "Directory"
        elif isinstance(typ, cli_types.CliString):
            return "string"
        elif isinstance(typ, cli_types.CliFloat):
            return "double"
        elif isinstance(typ, cli_types.CliInteger):
            return "long"
        elif isinstance(typ, cli_types.CliBoolean):
            return "boolean"
        elif isinstance(typ, cli_types.CliEnum):
            return "string"
        elif isinstance(typ, cli_types.CliList):
            return CwlGenerator.to_cwl_type(typ.value) + "[]"
        elif isinstance(typ, cli_types.CliTuple):
            return [CwlGenerator.to_cwl_type(subtype) for subtype in set(typ.values)]
        else:
            raise Exception(f"Invalid type {typ}!")

    def command_to_tool(self, cmd: Command) -> CommandLineTool:
        """
        Outputs the CWL wrapper to the provided file
        """
        tool = with_default_none(
            CommandLineTool,
            id=cmd.as_filename + ".cwl",
            baseCommand=list(cmd.command),
            cwlVersion="v1.1",
            inputs=[],
            outputs=[],
        )

        if not self.ignore_positionals:
            for pos in cmd.positional:
                tool.inputs.append(
                    with_default_none(
                        CommandInputParameter,
                        id=self.choose_variable_name(pos),
                        type=self.to_cwl_type(pos.get_type()),
                        inputBinding=with_default_none(
                            CommandLineBinding, position=pos.position
                        ),
                        doc=pos.description,
                    )
                )

        for flag in cmd.named:
            tool.inputs.append(
                with_default_none(
                    CommandInputParameter,
                    id=self.choose_variable_name(flag),
                    type=self.to_cwl_type(flag.get_type()),
                    inputBinding=with_default_none(
                        CommandLineBinding, prefix=flag.longest_synonym
                    ),
                    doc=flag.description,
                )
            )
        return tool

    def generate_wrapper(self, cmd: Command) -> str:
        io = StringIO()
        yaml.dump(self.command_to_tool(cmd).save(), io)
        return io.getvalue()

    def generate_tree(self, cmd: Command, out_dir: Path) -> Generator[Path, None, None]:
        for command in cmd.command_tree():
            path = (out_dir / command.as_filename).with_suffix(".cwl")
            with path.open("w") as fp:
                yaml.dump(self.command_to_tool(command).save(), fp)
            yield path
