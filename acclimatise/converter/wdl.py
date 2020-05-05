"""
Functions for generating WDL from the CLI data model
"""
from pathlib import Path
from typing import Generator, Iterable, List

from inflection import camelize
from wdlgen import ArrayType, Input, PrimitiveType, Task, WdlType

from acclimatise import cli_types, model
from acclimatise.converter import WrapperGenerator
from acclimatise.model import Command


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


def lowest_common_type(types: Iterable[cli_types.CliType]):
    type_set = {type(t) for t in types}

    if len(type_set) == 1:
        # If there is only one type, use it
        return type_set.pop()

    if (
        len(type_set) == 2
        and cli_types.CliInteger in type_set
        and cli_types.CliFloat in type_set
    ):
        # If they're all numeric, they can be represented as floats
        return cli_types.CliFloat()

    if {
        cli_types.CliDir,
        cli_types.CliDict,
        cli_types.CliFile,
        cli_types.CliTuple,
        cli_types.CliList,
    } & type_set:
        # These complex types cannot be represented in a simpler way
        raise Exception(
            "There is no common type between {}".format(", ".join(type_set))
        )

    else:
        # Most of the time, strings can be used to represent primitive types
        return cli_types.CliString()


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
                return WdlType(
                    ArrayType(
                        cls.type_to_wdl(lowest_common_type(typ.values)),
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

    def generate_wrapper(self, cmd: Command) -> str:
        name = cmd.as_filename
        task_name = camelize(name)

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
            name=task_name,
            command=Task.Command(
                command=" ".join(cmd.command),
                inputs=[flag_to_command_input(pos) for pos in cmd.positional],
                arguments=[flag_to_command_input(named) for named in cmd.named],
            ),
            version="1.0",
            inputs=inputs,
        )

        return tool.get_string()

    def generate_tree(self, cmd: Command, out_dir: Path) -> Generator[Path, None, None]:
        out_dir = Path(out_dir)
        for command in cmd.command_tree():
            name = command.as_filename
            path = (out_dir / name).with_suffix(".wdl")
            wrapper = self.generate_wrapper(command)
            path.write_text(wrapper, encoding="utf-8")
            yield path
