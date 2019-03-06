from declivity.parser import Command
from declivity import types
import jinja2
import subprocess


def type_to_wdl(typ: types.CliType) -> str:
    if isinstance(typ, types.CliString):
        return 'String'
    elif isinstance(typ, types.CliFloat):
        return 'Float'
    elif isinstance(typ, types.CliBoolean):
        return 'Boolean'
    elif isinstance(typ, types.CliInteger):
        return 'Integer'
    elif isinstance(typ, types.CliFile):
        return 'File'
    elif isinstance(typ, types.CliTuple):
        return 'Array[String]'
    else:
        return 'A'


def formulate_command(cmd: Command) -> str:
    args = subprocess.list2cmdline(cmd.command)

    for flag in cmd.flags:
        args += ' \\\n\t'
        args += '~{{"{} " + {}}}'.format(flag.longest_synonym.name, flag.name)

    return args


env = jinja2.Environment(
    loader=jinja2.PackageLoader('declivity', 'converter'),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)


def make_tasks(cmd: Command):
    template = env.get_template('wdl.jinja2')
    return template.render(
        taskname=''.join([token.capitalize() for token in cmd.command]),
        inputs=[(type_to_wdl(flag.longest_synonym.argtype.get_type()), flag.name) for flag in cmd.flags],
        command=formulate_command(cmd)
    )
