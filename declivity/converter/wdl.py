from declivity.parser import Command
from declivity import types
import jinja2


def type_to_wdl(typ: types.CliType) -> str:
    if isinstance(typ, types.CliString):
        return 'String'
    elif isinstance(typ, types.CliFloat):
        return 'Float'
    elif isinstance(typ, types.CliBoolean):
        return 'Boolean'
    elif isinstance(typ, types.CliInteger):
        return 'Integer'


env = jinja2.Environment(
    loader=jinja2.PackageLoader('declivity', 'converter'),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)


def make_tasks(cmd: Command):
    template = env.get_template('wdl.jinja2')
    print(template.render(
        taskname=cmd.command.capitalize(),
        inputs=cmd.flags,
        command=cmd.command
    ))
