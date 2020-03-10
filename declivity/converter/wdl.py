"""
Functions for generating WDL from the CLI data model
"""
import subprocess
from declivity import cli_types, jinja, model
from declivity.parser import Command
from declivity.converter import WrapperGenerator
import re
from inflection import camelize
from dataclasses import dataclass
from wdlgen import WdlType, ArrayType, PrimitiveType, Task, Input


class WdlGenerator(WrapperGenerator):
    case = 'snake'

    @classmethod
    def type_to_wdl(cls, typ: cli_types.CliType,
                    optional: bool = False) -> WdlType:
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
                return WdlType(ArrayType(
                    cls.type_to_wdl(typ.values[0]),
                    requires_multiple=not optional))
            else:
                raise Exception("WDL can't deal with hetrogenous array types")
        elif isinstance(typ, cli_types.CliList):
            return WdlType(ArrayType(
                cls.type_to_wdl(typ.value),
                requires_multiple=not optional)
            )
        elif isinstance(typ, cli_types.CliEnum):
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)
        else:
            return WdlType(PrimitiveType(PrimitiveType.kString), optional=optional)

    def formulate_command(self, cmd: Command) -> str:
        args = subprocess.list2cmdline(cmd.command)

        for flag in cmd.named:
            args += ' \\\n\t'
            if isinstance(flag.args.get_type(), cli_types.CliBoolean):
                args += '~{{true="{}" false="" {}}}'.format(flag.longest_synonym,
                                                            self.choose_variable_name(
                                                                flag))
            else:
                args += '~{{"{} " + {}}}'.format(flag.longest_synonym,
                                                 self.choose_variable_name(flag))

        return args

    @staticmethod
    def sanitize_wdl_str(string: str):
        return (
            re.sub('\)', ']',  # Replace left paren with a bracket
                   re.sub('\(', '[',  # Replace right paren with a bracket
                          re.sub('"', "'",  # Remote double quote string
                                 re.sub('[{}]', '', string  # Remove braces
                                        )
                                 )
                          )
                   )

        )

    def generate_wrapper(self, cmd: Command) -> str:
        env = jinja.get_env()
        env.filters['type_to_wdl'] = self.type_to_wdl
        env.filters['choose_variable_name'] = self.choose_variable_name
        env.filters['sanitize_str'] = self.sanitize_wdl_str

        name = camelize('_'.join(cmd.command).replace('-', '_'))

        tool = Task(
            name=name,
            command=Task.Command(
                command=cmd.command,
                inputs=[Task.Command.CommandInput(
                    name=pos.name_to_camel(),
                    optional=False,
                    position=pos.position
                ) for pos in cmd.positional],
                arguments=[Task.Command.CommandInput(
                    name=named.name_to_camel(),
                    prefix=named.longest_synonym,
                    optional=True

                ) for named in cmd.named]
            ),
            version="1.0",
            inputs=[Input(
                data_type=self.type_to_wdl(pos.get_type(), optional=False),
                name=pos.name_to_camel(),
            ) for pos in cmd.named] + [Input(
                data_type=self.type_to_wdl(pos.get_type(), optional=True),
                name=pos.name_to_camel(),
            ) for pos in cmd.positional]
        )

        return tool.get_string()

        # return template.render(
        #     taskname=name,
        #     positional=cmd.positional,
        #     named=cmd.named,
        #     command=self.formulate_command(cmd),
        #     generate_names=self.generate_names
        # )
