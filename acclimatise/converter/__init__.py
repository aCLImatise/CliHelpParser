from abc import abstractmethod
from dataclasses import dataclass

from acclimatise.model import CliArgument, Command

cases = ["snake", "camel"]


@dataclass
class WrapperGenerator:
    """
    Abstract base class for a class that converts a Command object into a string that defines a tool
    wrapper in a certain workflow language
    """

    @classmethod
    def choose_converter(cls, typ):
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
        Abstract method that defines the interface for converting a Command into a wrapper string
        """
        pass

    def choose_variable_name(self, flag: CliArgument) -> str:
        """
        Choose a name for this flag (e.g. the variable name when this is used to generate code), based on whether
        the user wants an auto generated one or not
        """
        if self.generate_names:
            return flag.generate_name()
        elif self.case == "snake":
            return flag.name_to_snake()
        elif self.case == "camel":
            return flag.name_to_camel()

    case: str = "snake"
    """
    Which case to use for variable names
    """

    generate_names: bool = False
    """
    Rather than using the long flag to generate the argument name, generate them automatically using the
    flag description. Generally helpful if there are no long flags, only short flags.
    """

    ignore_positionals: bool = False
    """
    Don't include positional arguments, for example because the help formatting has some
    misleading sections that look like positional arguments
    """
