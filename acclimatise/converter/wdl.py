"""
Functions for generating WDL from the CLI data model
"""
import re
import subprocess
from dataclasses import dataclass

from acclimatise import cli_types, model
from acclimatise.converter import WrapperGenerator
from acclimatise.model import Command
from inflection import camelize
from wdlgen import ArrayType, Input, PrimitiveType, Task, WdlType


def flag_to_command_input(flag: model.CliArgument) -> Task.Command.CommandInput:
    args = dict(name=flag.name_to_camel())

    if isinstance(flag, model.Flag):
        args.update(dict(optional=True,))
        if isinstance(flag.args, model.EmptyFlagArg):
            args.update(dict(true=flag.longest_synonym, false=""))
        else:
            args.update(dict(prefix=flag.longest_synonym,))
    elif isinstance(flag, model.Positional):
        args.update(dict(optional=False, position=flag.position))

    return Task.Command.CommandInput(**args)


class WdlGenerator(WrapperGenerator):
    case = "snake"

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
                raise Exception("WDL can't deal with hetrogenous array types")
        elif isinstance(typ, cli_types.CliList):
            return WdlType(
                ArrayType(cls.type_to_wdl(typ.value), requires_multiple=not optional)
            )
        elif isinstance(typ, cli_types.CliEnum):
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)
        else:
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)

    def formulate_command(self, cmd: Command) -> str:
        args = subprocess.list2cmdline(cmd.command)

        for flag in cmd.named:
            args += " \\\n\t"
            if isinstance(flag.args.get_type(), cli_types.CliBoolean):
                args += '~{{true="{}" false="" {}}}'.format(
                    flag.longest_synonym, self.choose_variable_name(flag)
                )
            else:
                args += '~{{"{} " + {}}}'.format(
                    flag.longest_synonym, self.choose_variable_name(flag)
                )

        return args

    @staticmethod
    def sanitize_wdl_str(string: str):
        return re.sub(
            "\)",
            "]",  # Replace left paren with a bracket
            re.sub(
                "\(",
                "[",  # Replace right paren with a bracket
                re.sub(
                    '"',
                    "'",  # Remote double quote string
                    re.sub("[{}]", "", string),  # Remove braces
                ),
            ),
        )

    def generate_wrapper(self, cmd: Command) -> str:
        name = camelize("_".join(cmd.command).replace("-", "_"))

        inputs = [
            Input(
                data_type=self.type_to_wdl(pos.get_type(), optional=False),
                name=pos.name_to_camel(),
            )
            for pos in cmd.named
        ]
        if not self.ignore_positionals:
            inputs += [
                Input(
                    data_type=self.type_to_wdl(pos.get_type(), optional=True),
                    name=pos.name_to_camel(),
                )
                for pos in cmd.positional
            ]

        tool = Task(
            name=name,
            command=Task.Command(
                command=" ".join(cmd.command),
                inputs=[flag_to_command_input(pos) for pos in cmd.positional],
                arguments=[flag_to_command_input(named) for named in cmd.named],
            ),
            version="1.0",
            inputs=inputs,
        )

        return tool.get_string()

        # return template.render(
        #     taskname=name,
        #     positional=cmd.positional,
        #     named=cmd.named,
        #     command=self.formulate_command(cmd),
        #     generate_names=self.generate_names
        # )
