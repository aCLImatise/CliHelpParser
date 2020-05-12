from abc import abstractmethod
from pathlib import Path
from typing import Iterable, List, Type

from dataclasses import dataclass

from acclimatise.model import CliArgument, Command
from acclimatise.name_generation import name_to_camel, name_to_snake


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

    def choose_variable_name(self, flag: CliArgument) -> str:
        """
        Choose a name for this flag (e.g. the variable name when this is used to generate code), based on whether
        the user wants an auto generated one or not
        """
        # Choose the best name if we're allowed to, otherwise always use the argument-based name
        if self.generate_names:
            toks = flag.variable_name
        else:
            toks = flag._name_from_name

        if self.case == "snake":
            return name_to_snake(toks)
        elif self.case == "camel":
            return name_to_camel(toks)

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
