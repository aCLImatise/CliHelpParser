"""
Functions for generating WDL from the CLI data model
"""
import subprocess
from declivity import cli_types, jinja, model
from declivity.parser import Command
from declivity.converter import WrapperGenerator
import re


class WdlGenerator(WrapperGenerator):

    @classmethod
    def type_to_wdl(cls, typ: cli_types.CliType, optional: bool = False) -> str:
        if isinstance(typ, cli_types.CliString):
            wdl_type = 'String'
        elif isinstance(typ, cli_types.CliFloat):
            wdl_type = 'Float'
        elif isinstance(typ, cli_types.CliBoolean):
            wdl_type = 'Boolean'
        elif isinstance(typ, cli_types.CliInteger):
            wdl_type = 'Integer'
        elif isinstance(typ, cli_types.CliFile):
            wdl_type = 'File'
        elif isinstance(typ, cli_types.CliTuple):
            wdl_type = 'Array[String]'
        elif isinstance(typ, cli_types.CliEnum):
            wdl_type = 'String'
        elif isinstance(typ, cli_types.CliList):
            inner_type = cls.type_to_wdl(typ.value)
            wdl_type = f'Array[{inner_type}]'
        elif isinstance(typ, cli_types.CliDir):
            wdl_type = 'File'
        else:
            raise Exception('Unknown CliType')

        if optional:
            return wdl_type + '?'
        else:
            return wdl_type

    def formulate_command(self, cmd: Command) -> str:
        args = subprocess.list2cmdline(cmd.command)

        for flag in cmd.named:
            args += ' \\\n\t'
            if isinstance(flag.args.get_type(), cli_types.CliBoolean):
                args += '~{{true="{}" false="" {}}}'.format(flag.longest_synonym, self.choose_variable_name(flag, format='snake'))
            else:
                args += '~{{"{} " + {}}}'.format(flag.longest_synonym, self.choose_variable_name(flag, format='snake'))

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
        template = env.get_template('wdl.jinja2')
        return template.render(
            taskname=''.join([token.capitalize() for token in cmd.command]),
            positional=cmd.positional,
            named=cmd.named,
            command=self.formulate_command(cmd),
            generate_names=self.generate_names
        )
