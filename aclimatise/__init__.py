import typing

from aclimatise.converter import WrapperGenerator
from aclimatise.converter.cwl import CwlGenerator
from aclimatise.converter.wdl import WdlGenerator
from aclimatise.converter.yml import YmlGenerator
from aclimatise.execution import Executor
from aclimatise.execution.docker import DockerExecutor
from aclimatise.execution.local import LocalExecutor
from aclimatise.execution.man import ManPageExecutor
from aclimatise.integration import parse_help
from aclimatise.model import Command, Flag
from deprecated import deprecated

default_executor = LocalExecutor()


@deprecated(
    reason="Please use the explore method on the executors directly. e.g. `LocalExecutor().explore()`"
)
def explore_command(
    cmd: typing.List[str],
    flags: typing.Iterable[str] = (["--help"], ["-h"], [], ["--usage"]),
    parent: typing.Optional[Command] = None,
    max_depth: int = 2,
    try_subcommand_flags=True,
    executor: Executor = default_executor,
) -> typing.Optional[Command]:
    """
    Given a command to start with, builds a model of this command and all its subcommands (if they exist).
    Use this if you know the command you want to parse, you don't know which flags it responds to with help text, and
    you want to include subcommands.
    """
    return executor.explore(cmd, max_depth=max_depth, parent=parent)


__all__ = [
    CwlGenerator,
    WdlGenerator,
    YmlGenerator,
    LocalExecutor,
    DockerExecutor,
    ManPageExecutor,
    explore_command,
    parse_help,
]
