import abc
import copy
import logging
from typing import Iterable, List, Optional

from pyparsing import ParseBaseException

from aclimatise.execution import Executor
from aclimatise.integration import parse_help
from aclimatise.model import Command

logger = logging.getLogger()


class CliHelpExecutor(Executor):
    """
    This is an abstract class for any executor that works with command-line help conventions like using help flags in
    order to obtain the help text.
    """

    def __init__(
        self,
        flags: Iterable[str] = (["--help"], ["-h"], [], ["--usage"]),
        try_subcommand_flags=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.flags = flags
        self.try_subcommand_flags = try_subcommand_flags

    def explore(
        self,
        command: List[str],
        max_depth: int = 2,
        parent: Optional[Command] = None,
    ) -> Optional[Command]:

        logger.info("Exploring {}".format(" ".join(command)))
        best = self.convert(command)
        best.parent = parent

        # Check if this is a valid subcommand
        if parent:
            if best.valid_subcommand():
                logger.info(
                    "{} seems to be a valid subcommand".format(" ".join(command))
                )
            else:
                logger.info(
                    "{} does not seem to be a valid subcommand".format(
                        " ".join(command)
                    )
                )
                return None

        # Recursively call this function on positionals, but only do this if we aren't at max depth
        if best.depth < max_depth:
            # By default we use the best parent help-flag
            child_executor = copy.copy(self)
            child_executor.flags = (
                self.flags if self.try_subcommand_flags else [best.generated_using]
            )

            # Try each *unique* positional
            for positional in {positional.name for positional in best.positional}:
                subcommand = child_executor.explore(
                    command=command + [positional],
                    parent=best,
                    max_depth=max_depth,
                )
                if subcommand is not None:
                    best.subcommands.append(subcommand)
                    # If we had any subcommands then we probably don't have any positionals, or at least don't care about them
                    best.positional = []

        return best

    @abc.abstractmethod
    def execute(self, cmd: List[str]) -> str:
        """
        Executes the provided command and returns a string containing the output
        """
        pass

    def convert(
        self,
        cmd: List[str],
    ) -> Command:
        """
        Determine the best Command instance for a given command line tool, by trying many
        different help flags, such as --help and -h, then return the Command. Use this if you know the command you want to
        parse, but you don't know which flags it responds to with help text. Unlike :py:func:`aclimatise.explore_command`,
        this doesn't even attempt to parse subcommands.

        :param cmd: The command to analyse, e.g. ['wc'] or ['bwa', 'mem']
        :param flags: A list of help flags to try, e.g. ['--help', '-h'], in order how which one you would prefer to use.
        Generally [] aka no flags should be last
        :param executor: A class that provides the means to run a command. You can use the pre-made classes or write your own.
        """
        # For each help flag, run the command and then try to parse it
        logger.info("Trying flags for {}".format(" ".join(cmd)))
        commands = []
        for flag in self.flags:
            help_cmd = cmd + flag
            logger.info("Trying {}".format(" ".join(help_cmd)))
            try:
                final = self.execute(help_cmd)
                result = parse_help(cmd, final, max_length=self.max_length)
                result.generated_using = flag
                commands.append(result)
            except (ParseBaseException, UnicodeDecodeError) as e:
                # If parsing fails, this wasn't the right flag to use
                continue

        # Sort by flags primarily, and if they're equal, return the command with the longest help text, and if they're equal
        # return the command with the most help flags. This helps ensure we get ["bedtools", "--help"] instead of
        # ["bedtools"]
        best = Command.best(commands)
        logger.info(
            "The best help flag seems to be {}".format(
                " ".join(best.command + best.generated_using)
            )
        )
        return best
