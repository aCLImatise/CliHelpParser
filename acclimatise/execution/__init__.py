"""
This module is concerned with running the actual commands so that we can parse their output
"""
import abc
from typing import List


class Executor(abc.ABC):
    """
    An executor is anything that can take a command such as ["bwa"] or ["samtools", "sort"] and return the output
    """

    @abc.abstractmethod
    def execute(self, command: List[str]) -> str:
        """
        Execute a command defined by a list of arguments, and return the result as a string
        """
        pass
