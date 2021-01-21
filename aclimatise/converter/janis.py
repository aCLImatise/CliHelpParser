from typing import List

import janis_core as janis
from aclimatise import cli_types
from aclimatise.cli_types import CliType
from aclimatise.converter import NamedArgument, WrapperGenerator
from aclimatise.model import CliArgument, Command, Flag, Positional


class JanisGenerator(WrapperGenerator):
    @classmethod
    def format(cls) -> str:
        return "janis"

    def save_to_string(self, cmd: Command) -> str:

        clt = self.command_to_tool(cmd)
        return clt.translate("janis", to_console=False)

    def command_to_tool(self, cmd: Command) -> janis.CommandToolBuilder:

        inputs: List[CliArgument] = [*cmd.named] + (
            [] if self.ignore_positionals else [*cmd.positional]
        )
        names = self.choose_variable_names(inputs)

        tool = janis.CommandToolBuilder(
            tool=cmd.as_filename,
            base_command=list(cmd.command),
            inputs=self.get_inputs(names),
            outputs=self.get_outputs(names),
            version="v0.1.0",
            container=cmd.docker_image,
        )

        return tool

    def type_to_janis_type(
        self, typ: cli_types.CliType, optional: bool
    ) -> janis.DataType:

        if isinstance(typ, cli_types.CliFile):
            return janis.File(optional=optional)
        elif isinstance(typ, cli_types.CliDir):
            return janis.Directory(optional=optional)
        elif isinstance(typ, cli_types.CliString):
            return janis.String(optional=optional)
        elif isinstance(typ, cli_types.CliFloat):
            return janis.Float(optional=optional)
        elif isinstance(typ, cli_types.CliInteger):
            return janis.Int(optional=optional)
        elif isinstance(typ, cli_types.CliBoolean):
            return janis.Boolean(optional=optional)
        elif isinstance(typ, cli_types.CliEnum):
            return janis.String(optional=optional)
        elif isinstance(typ, cli_types.CliList):
            # TODO: how is Array<String?> represented?
            inner = self.type_to_janis_type(typ.value, optional=False)
            return janis.Array(inner, optional=optional)

        elif isinstance(typ, cli_types.CliTuple):
            return self.type_to_janis_type(
                CliType.lowest_common_type(typ.values), optional=False
            )
        else:
            raise Exception(f"Invalid type {typ}!")

    def arg_to_janis_type(self, arg: CliArgument) -> janis.DataType:
        return self.type_to_janis_type(arg.get_type(), arg.optional)

    def get_inputs(self, names: List[NamedArgument]) -> List[janis.ToolInput]:
        ret = []
        for arg in names:
            assert arg.name != "", arg
            ret.append(
                janis.ToolInput(
                    tag="in_" + arg.name,
                    input_type=self.arg_to_janis_type(arg.arg),
                    position=arg.arg.position
                    if isinstance(arg.arg, Positional)
                    else None,
                    prefix=arg.arg.longest_synonym
                    if isinstance(arg.arg, Flag)
                    else None,
                    doc=arg.arg.description,
                )
            )
        return ret

    def get_outputs(self, names: List[NamedArgument]) -> List[janis.ToolOutput]:
        ret = []
        for arg in names:
            typ = arg.arg.get_type()
            if isinstance(typ, cli_types.CliFileSystemType) and typ.output:
                ret.append(
                    janis.ToolOutput(
                        tag="out_" + arg.name,
                        output_type=self.arg_to_janis_type(arg.arg),
                        doc=arg.arg.description,
                        selector=janis.InputSelector("in_" + arg.name),
                    )
                )
        return ret

    @property
    def suffix(self) -> str:
        return ".py"
