import tempfile
from dataclasses import dataclass

import cwlgen
from acclimatise import cli_types
from acclimatise.converter import WrapperGenerator
from acclimatise.model import Command


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

    def generate_wrapper(self, cmd: Command) -> str:
        cwl_tool = cwlgen.CommandLineTool(
            tool_id=self.snake_case(cmd.command),
            base_command=cmd.command,
            cwl_version="v1.0",
        )

        if not self.ignore_positionals:
            for pos in cmd.positional:
                cwl_tool.inputs.append(
                    cwlgen.CommandInputParameter(
                        param_id=self.choose_variable_name(pos),
                        param_type=self.to_cwl_type(pos.get_type()),
                        input_binding=cwlgen.CommandLineBinding(position=pos.position),
                        doc=pos.description,
                    )
                )

        for flag in cmd.named:
            cwl_tool.inputs.append(
                cwlgen.CommandInputParameter(
                    param_id=self.choose_variable_name(flag),
                    param_type=self.to_cwl_type(flag.get_type()),
                    input_binding=cwlgen.CommandLineBinding(
                        prefix=flag.longest_synonym
                    ),
                    doc=flag.description,
                )
            )

        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as temp:
            cwl_tool.export(temp.name)
            return temp.read()
