import inspect
import tempfile
from io import IOBase, StringIO, TextIOBase
from os import PathLike
from pathlib import Path
from typing import Generator, List

from cwl_utils.parser_v1_1 import (
    CommandInputParameter,
    CommandLineBinding,
    CommandLineTool,
)
from dataclasses import dataclass

from acclimatise import cli_types
from acclimatise.converter import NamedArgument, WrapperGenerator
from acclimatise.model import CliArgument, Command, Flag, Positional
from acclimatise.yaml import yaml

# def with_default_none(func, *args, **kwargs):
#     """
#     Calls a function, and inserts None for all arguments you didn't provide
#     """
#     spec = inspect.getfullargspec(func)
#     defaults = {arg: None for arg in spec.args}
#     defaults.pop("self", None)
#     return func(*args, **{**defaults, **kwargs})


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
        inputs: List[CliArgument] = [*cmd.named] + (
            [] if self.ignore_positionals else [*cmd.positional]
        )
        names = self.choose_variable_names(inputs)

        tool = CommandLineTool(
            id=cmd.as_filename + ".cwl",
            baseCommand=list(cmd.command),
            cwlVersion="v1.1",
            inputs=[],
            outputs=[],
        )

        for arg in names:
            assert arg.name != "", arg
            tool.inputs.append(
                CommandInputParameter(
                    id=arg.name,
                    type=self.to_cwl_type(arg.arg.get_type()),
                    inputBinding=CommandLineBinding(
                        position=arg.arg.position
                        if isinstance(arg.arg, Positional)
                        else None,
                        prefix=arg.arg.longest_synonym
                        if isinstance(arg.arg, Flag)
                        else None,
                    ),
                    doc=arg.arg.description,
                )
            )
        return tool

    @property
    def suffix(self) -> str:
        return ".cwl"

    def save_to_string(self, cmd: Command) -> str:
        io = StringIO()
        yaml.dump(self.command_to_tool(cmd).save(), io)
        return io.getvalue()

    def save_to_file(self, cmd: Command, path: Path) -> None:
        map = self.command_to_tool(cmd).save(base_url=str(path))
        with path.open("w") as fp:
            yaml.dump(map, fp)
