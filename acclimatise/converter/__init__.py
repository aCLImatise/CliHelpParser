from abc import abstractmethod
from itertools import groupby, zip_longest
from pathlib import Path
from typing import Iterable, List, Type

from dataclasses import dataclass

from acclimatise.model import CliArgument, Command, Flag
from acclimatise.name_generation import (
    choose_unique_name,
    generate_name,
    generate_names_nlp,
    generate_names_segment,
    name_to_camel,
    name_to_snake,
)


@dataclass
class NamedArgument:
    arg: CliArgument
    name: str


@dataclass
class WrapperGenerator:
    """
    Abstract base class for a class that converts a Command object into a string that defines a tool
    wrapper in a certain workflow language
    """

    cases = ["snake", "camel"]

    @classmethod
    def choose_converter(cls, typ) -> Type["WrapperGenerator"]:
        """
        Returns a converter subclass, given a converter type name
        :param type: The type of converter, e.g. 'cwl' or 'wdl'
        """
        for subclass in cls.__subclasses__():
            if subclass.format() == typ:
                return subclass

        raise Exception("Unknown format type")

    @classmethod
    @abstractmethod
    def format(cls) -> str:
        """
        Returns the output format that this generator produces as a string, e.g. "cwl"
        """
        pass

    @abstractmethod
    def generate_wrapper(self, cmd: Command) -> str:
        """
        Convert the command into a single string, ignoring subcommands
        """
        pass

    @abstractmethod
    def generate_tree(self, cmd: Command, out_dir: Path) -> Iterable[Path]:
        """
        Convert the command into a list of tool wrapper files
        """
        pass

    def words_to_name(self, words: Iterable[str]):
        """
        Converts a list of tokens, such as ["a", "variable", "name"] to a language-appropriate name, such as
        "aVariableName"
        """
        if self.case == "snake":
            return name_to_snake(words)
        elif self.case == "camel":
            return name_to_camel(words)

    def choose_variable_names(
        self, flags: List[CliArgument], length: int = 3
    ) -> List[NamedArgument]:
        """
        Choose names for a list of flags. This needs to be done in one go because there is a risk of duplicate
        variable names otherwise
        :param length: See :py:func:`acclimatise.name_generation.generate_name`
        """
        options = list(
            zip_longest(
                generate_names_segment([flag.full_name() for flag in flags]),
                generate_names_nlp([flag.description for flag in flags]),
                [flag.argument_name() for flag in flags if isinstance(flag, Flag)],
                fillvalue=[],
            )
        )

        return [
            NamedArgument(
                arg=flag, name=self.words_to_name(choose_unique_name(flag_options))
            )
            for flag, flag_options in zip(flags, options)
        ]

    case: str = "snake"
    """
    Which case to use for variable names
    """

    generate_names: bool = True
    """
    Rather than using the long flag to generate the argument name, generate them automatically using the
    flag description. Generally helpful if there are no long flags, only short flags.
    """

    ignore_positionals: bool = False
    """
    Don't include positional arguments, for example because the help formatting has some
    misleading sections that look like positional arguments
    """
