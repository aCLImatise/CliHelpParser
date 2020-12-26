from io import StringIO
from pathlib import Path
from typing import List

import attr
from cwl_utils.parser_v1_1 import (
    CommandInputParameter,
    CommandLineBinding,
    CommandLineTool,
    CommandOutputBinding,
    CommandOutputParameter,
    DockerRequirement,
)

from aclimatise import cli_types
from aclimatise.cli_types import CliType
from aclimatise.converter import NamedArgument, WrapperGenerator
from aclimatise.model import CliArgument, Command, Flag, Positional
from aclimatise.yaml import yaml


@attr.s(auto_attribs=True)
class CwlGenerator(WrapperGenerator):
    case = "snake"

    @classmethod
    def format(cls) -> str:
        return "cwl"

    @staticmethod
    def snake_case(words: list):
        return "_".join([word.lower() for word in words])

    @staticmethod
    def type_to_cwl_type(typ: cli_types.CliType) -> str:
        """
        Calculate the CWL type for a CLI type
        """
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
            return CwlGenerator.type_to_cwl_type(typ.value) + "[]"
        elif isinstance(typ, cli_types.CliTuple):
            return CwlGenerator.type_to_cwl_type(CliType.lowest_common_type(typ.values))
        else:
            raise Exception(f"Invalid type {typ}!")

    @staticmethod
    def arg_to_cwl_type(arg: CliArgument) -> str:
        """
        Calculate the CWL type for an entire argument
        """
        typ = arg.get_type()
        cwl_type = CwlGenerator.type_to_cwl_type(typ)

        if arg.optional and not cwl_type.endswith("[]"):
            return cwl_type + "?"
        else:
            return cwl_type

    def get_inputs(self, names: List[NamedArgument]) -> List[CommandInputParameter]:
        ret = []
        for arg in names:
            assert arg.name != "", arg
            ret.append(
                CommandInputParameter(
                    id="in_" + arg.name,
                    type=self.arg_to_cwl_type(arg.arg),
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

        return ret

    def get_outputs(self, names: List[NamedArgument]) -> List[CommandOutputParameter]:
        ret = [
            # We default to always capturing stdout
            CommandOutputParameter(
                id="out_stdout",
                type="stdout",
                doc="Standard output stream",
            )
        ]

        for arg in names:
            typ = arg.arg.get_type()
            if isinstance(typ, cli_types.CliFileSystemType) and typ.output:
                ret.append(
                    CommandOutputParameter(
                        id="out_" + arg.name,
                        type=self.arg_to_cwl_type(arg.arg),
                        doc=arg.arg.description,
                        outputBinding=CommandOutputBinding(
                            glob="$(inputs.in_{})".format(arg.name)
                        ),
                    )
                )
        return ret

    def command_to_tool(self, cmd: Command) -> CommandLineTool:
        """
        Outputs the CWL wrapper to the provided file
        """
        inputs: List[CliArgument] = [*cmd.named] + (
            [] if self.ignore_positionals else [*cmd.positional]
        )
        names = self.choose_variable_names(inputs)

        hints = []
        if cmd.docker_image is not None:
            hints.append(DockerRequirement(dockerPull=cmd.docker_image))

        tool = CommandLineTool(
            id=cmd.as_filename + ".cwl",
            baseCommand=list(cmd.command),
            cwlVersion="v1.1",
            inputs=self.get_inputs(names),
            outputs=self.get_outputs(names),
            hints=hints,
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
        map = self.command_to_tool(cmd).save()
        with path.open("w") as fp:
            yaml.dump(map, fp)
