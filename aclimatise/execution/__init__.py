"""
This module is concerned with running the actual commands so that we can parse their output
"""
import abc
from typing import List, Optional

from aclimatise.model import Command


class Executor(abc.ABC):
    """
    An executor is anything that can take a command such as ["bwa"] or
    ["samtools", "sort"] and return the help output
    """

    def __init__(
        self, timeout: int = 10, raise_on_timout=False, max_length: Optional[int] = 1000
    ):
        """
        :param timeout: Amount of inactivity before the execution will be killed
        :param raise_on_timout: If true, execute will raise a TimeoutError if it
            times out
        """
        # Here we initialise all shared parameters that are used by all executors
        self.timeout = timeout
        self.raise_on_timeout = raise_on_timout
        self.max_length = max_length

    def handle_timeout(self, e: Exception) -> str:
        """
        Subclasses can call this when a timeout has occurred
        :param e: The timeout exception that caused the timeout
        """
        if self.raise_on_timeout:
            raise TimeoutError()
        else:
            return ""

    def explore(
        self,
        command: List[str],
        max_depth: int = 2,
        parent: Optional[Command] = None,
    ) -> Command:
        """
        Given a command to start with, builds a model of this command and all its subcommands (if they exist)
        """
        # If the executor doesn't implement a specific exploration technique, we just execute and ignore subcommands
        return self.convert(command)

    @abc.abstractmethod
    def convert(self, command: List[str]) -> Command:
        """
        Convert a single executable to a Command object, without considering subcommands
        """
        pass
