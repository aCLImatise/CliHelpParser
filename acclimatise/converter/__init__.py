from abc import abstractmethod
from itertools import groupby
from pathlib import Path
from typing import Iterable, List, Type

from dataclasses import dataclass

from acclimatise.model import CliArgument, Command
from acclimatise.name_generation import (
    generate_name,
    generate_names,
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

    def choose_variable_name(
        self, flag: CliArgument, min: int = None, max: int = None
    ) -> str:
        """
        Choose a name for this flag (e.g. the variable name when this is used to generate code), based on whether
        the user wants an auto generated one or not
        """
        raise DeprecationWarning("Use choose_variables_names() instead")
        # Choose the best name if we're allowed to, otherwise always use the argument-based name
        if self.generate_names:
            toks = flag.variable_name(min=min, max=max)
        else:
            toks = flag._name_from_name()

        return self.words_to_name(toks)

    def choose_variable_names(
        self, flags: List[CliArgument], length: int = 3
    ) -> List[NamedArgument]:
        """
        Choose names for a list of flags. This needs to be done in one go because there is a risk of duplicate
        variable names otherwise
        :param length: See :py:func:`acclimatise.name_generation.generate_name`
        """

        if self.generate_names:
            # If we are allowed to generate names, generate the whole batch, and then choose the best method of
            # name generation on a case-by-case basis
            names = generate_names([flag.description for flag in flags], length=length)
            return [
                NamedArgument(
                    name=self.words_to_name(flag.variable_name(name)), arg=flag
                )
                for name, flag in zip(names, flags)
            ]
        else:
            # If we aren't allowed to generate names, always use the flag name as the variable name
            return [
                NamedArgument(name=self.words_to_name(flag._name_from_name()), arg=flag)
                for flag in flags
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
