"""
Functions for generating WDL from the CLI data model
"""
import re
from typing import Iterable, List, Set, Tuple

from inflection import camelize
from WDL._grammar import keywords
from wdlgen import (
    ArrayType,
    File,
    Input,
    Output,
    ParameterMeta,
    PrimitiveType,
    Task,
    WdlType,
)

from aclimatise import cli_types, model
from aclimatise.converter import NamedArgument, WrapperGenerator
from aclimatise.model import CliArgument, Command, Flag, Positional
from aclimatise.nlp import wordsegment

#: A regex, borrowed from MiniWDL, that ma
WDL_IDENT = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")
#: Matches all characters we should remove from a WDL identifier
WDL_STRIP = re.compile(r"(^[^a-zA-Z])|([^a-zA-Z0-9_])")


def escape_wdl_str(text: str):
    """
    Escape literal quotes in a Python string, to become suitable for WDL
    """
    return text.replace('"', '\\"').replace("\n", "\\n")


def flag_to_command_input(
    named_flag: NamedArgument, converter: WrapperGenerator
) -> Task.Command.CommandInput:
    args = dict(name=named_flag.name)

    if isinstance(named_flag.arg, model.Flag):
        args.update(dict(optional=named_flag.arg.optional))
        if isinstance(named_flag.arg.args, model.EmptyFlagArg):
            args.update(dict(true=named_flag.arg.longest_synonym, false=""))
        else:
            args.update(
                dict(
                    prefix=named_flag.arg.longest_synonym,
                )
            )
    elif isinstance(named_flag, model.Positional):
        args.update(dict(optional=False, position=named_flag.position))

    return Task.Command.CommandInput.from_fields(**args)


class WdlGenerator(WrapperGenerator):
    @property
    def suffix(self) -> str:
        return ".wdl"

    case = "snake"

    @property
    def reserved(self) -> Set[Tuple[str, ...]]:
        # Steal the keywords list from miniWDL
        return {tuple(wordsegment.segment(key)) for key in keywords["1.0"]}

    @classmethod
    def format(cls) -> str:
        return "wdl"

    @classmethod
    def type_to_wdl(cls, typ: cli_types.CliType, optional: bool = False) -> WdlType:
        if isinstance(typ, cli_types.CliString):
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)
        elif isinstance(typ, cli_types.CliFloat):
            return WdlType(PrimitiveType(PrimitiveType.kFloat), optional=optional)
        elif isinstance(typ, cli_types.CliBoolean):
            return WdlType(PrimitiveType(PrimitiveType.kBoolean), optional=optional)
        elif isinstance(typ, cli_types.CliInteger):
            return WdlType(PrimitiveType(PrimitiveType.kInt), optional=optional)
        elif isinstance(typ, cli_types.CliFile):
            return WdlType(PrimitiveType(PrimitiveType.kFile), optional=optional)
        elif isinstance(typ, cli_types.CliDir):
            return WdlType(PrimitiveType(PrimitiveType.kDirectory), optional=optional)
        elif isinstance(typ, cli_types.CliTuple):
            if typ.homogenous:
                return WdlType(
                    ArrayType(
                        cls.type_to_wdl(typ.values[0]), requires_multiple=not optional
                    )
                )
            else:
                return WdlType(
                    ArrayType(
                        cls.type_to_wdl(
                            cli_types.CliType.lowest_common_type(typ.values)
                        ),
                        requires_multiple=not optional,
                    )
                )
        elif isinstance(typ, cli_types.CliList):
            return WdlType(
                ArrayType(cls.type_to_wdl(typ.value), requires_multiple=not optional)
            )
        elif isinstance(typ, cli_types.CliEnum):
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)
        else:
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)

    def make_inputs(self, named: Iterable[NamedArgument]) -> List[Input]:
        return [
            Input(
                data_type=self.type_to_wdl(
                    named_arg.arg.get_type(), optional=named_arg.arg.optional
                ),
                name=named_arg.name,
            )
            for named_arg in named
        ]

    def make_command(self, cmd: Command, inputs: List[NamedArgument]) -> Task.Command:
        return Task.Command(
            command=" ".join([WDL_STRIP.sub("_", tok) for tok in cmd.command]),
            inputs=[
                flag_to_command_input(input, self)
                for input in inputs
                if isinstance(input.arg, Positional)
            ],
            arguments=[
                flag_to_command_input(input, self)
                for input in inputs
                if isinstance(input.arg, Flag)
            ],
        )

    def make_parameter_meta(self, named: Iterable[NamedArgument]) -> ParameterMeta:
        params = {}
        for named_arg in named:
            params[named_arg.name] = escape_wdl_str(named_arg.arg.description)

        return ParameterMeta(**params)

    def make_task_name(self, cmd: Command) -> str:
        return camelize(
            "_".join([WDL_STRIP.sub("", token) for token in cmd.command]).replace(
                "-", "_"
            )
        )

    def make_outputs(self, names: List[NamedArgument]) -> List[Output]:
        ret = [
            # We default to always capturing stdout
            Output(data_type=File, name="out_stdout", expression="stdout()")
        ]
        for arg in names:
            typ = arg.arg.get_type()
            if isinstance(typ, cli_types.CliFileSystemType) and typ.output:
                ret.append(
                    Output(
                        data_type=self.type_to_wdl(typ),
                        name="out_" + arg.name,
                        expression='"${{in_{}}}"'.format(arg.name),
                    )
                )

        return ret

    def save_to_string(self, cmd: Command) -> str:
        inputs: List[CliArgument] = [*cmd.named] + (
            [] if self.ignore_positionals else [*cmd.positional]
        )
        names = self.choose_variable_names(inputs)
        runtime = Task.Runtime()
        runtime.add_docker(cmd.docker_image)

        tool = Task(
            name=self.make_task_name(cmd),
            command=self.make_command(cmd, names),
            version="1.0",
            inputs=self.make_inputs(names),
            outputs=self.make_outputs(names),
            parameter_meta=self.make_parameter_meta(names),
            runtime=runtime,
        )

        return tool.get_string()
