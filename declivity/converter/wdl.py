from declivity.parser import Command
import jinja2
import subprocess
from declivity import cli_types, jinja
import re


def type_to_wdl(typ: cli_types.CliType) -> str:
    if isinstance(typ, cli_types.CliString):
        return 'String'
    elif isinstance(typ, cli_types.CliFloat):
        return 'Float'
    elif isinstance(typ, cli_types.CliBoolean):
        return 'Boolean'
    elif isinstance(typ, cli_types.CliInteger):
        return 'Integer'
    elif isinstance(typ, cli_types.CliFile):
        return 'File'
    elif isinstance(typ, cli_types.CliTuple):
        return 'Array[String]'
    elif isinstance(typ, cli_types.CliEnum):
        return 'String'
    elif isinstance(typ, cli_types.CliList):
        inner_type = type_to_wdl(typ.value)
        return f'Array[{inner_type}]'
    else:
        raise Exception('Unknown CliType')


def formulate_command(cmd: Command) -> str:
    args = subprocess.list2cmdline(cmd.command)

    for flag in cmd.named:
        args += ' \\\n\t'
        if isinstance(flag.args.get_type(), cli_types.CliBoolean):
            args += '~{{true="{}" false="" {}}}'.format(flag.longest_synonym,
                                                        flag.synonym_to_snake(flag.longest_synonym))
        else:
            args += '~{{"{} " + {}}}'.format(flag.longest_synonym, flag.synonym_to_snake(flag.longest_synonym))

    return args


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


def make_tasks(cmd: Command):
    env = jinja.get_env()
    env.filters['type_to_wdl'] = type_to_wdl
    env.filters['sanitize_str'] = sanitize_wdl_str
    template = env.get_template('wdl.jinja2')
    return template.render(
        taskname=''.join([token.capitalize() for token in cmd.command]),
        named=cmd.named,
        command=formulate_command(cmd)
    )
