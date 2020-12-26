from abc import abstractmethod
from itertools import groupby, zip_longest
from os import PathLike
from pathlib import Path
from typing import Generator, Iterable, List, Set, TextIO, Tuple, Type

import attr

from aclimatise.model import CliArgument, Command, Flag
from aclimatise.name_generation import (
    NameGenerationError,
    choose_unique_name,
    generate_name,
    generate_names_nlp,
    generate_names_segment,
    name_to_camel,
    name_to_snake,
)
from aclimatise.yaml import AttrYamlMixin


@attr.s(
    auto_attribs=True,
)
class NamedArgument(AttrYamlMixin):
    arg: CliArgument
    name: str


@attr.s(
    auto_attribs=True,
)
class WrapperGenerator(AttrYamlMixin):
    """
    Abstract base class for a class that converts a Command object into a string that defines a tool
    wrapper in a certain workflow language
    """

    cases = ["snake", "camel"]

    @classmethod
    def get_subclasses(cls) -> List[Type["WrapperGenerator"]]:
        return cls.__subclasses__()

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
    def save_to_string(self, cmd: Command) -> str:
        """
        Convert the command into a single string, ignoring subcommands
        """
        pass

    def save_to_file(self, cmd: Command, path: Path) -> None:
        """
        Write the command into a file
        """
        # By default we just write the string out, but subclasses can have different behaviour
        path.write_text(self.save_to_string(cmd))

    def generate_tree(
        self, cmd: Command, out_dir: PathLike
    ) -> Generator[Tuple[Path, Command], None, None]:
        out_dir = Path(out_dir)
        for cmd in cmd.command_tree():
            path = out_dir / (cmd.as_filename + self.suffix)
            try:
                self.save_to_file(cmd, path)
            except NameGenerationError as e:
                raise NameGenerationError(
                    'Name generation error for command "{}". {}'.format(
                        " ".join(cmd.command), e.message
                    )
                )
            yield path, cmd

    @property
    def reserved(self) -> Set[Tuple[str, ...]]:
        """
        A list of reserved keywords for this language
        """
        return set()

    @property
    @abstractmethod
    def suffix(self) -> str:
        """
        Returns a suffix for files generated using this converter
        """

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
        :param length: See :py:func:`from aclimatise.name_generation.generate_name`
        """
        options = list(
            zip_longest(
                generate_names_segment([flag.full_name() for flag in flags]),
                generate_names_nlp(
                    [flag.description for flag in flags], reserved=self.reserved
                ),
                [flag.argument_name() for flag in flags if isinstance(flag, Flag)],
                fillvalue=[],
            )
        )

        return [
            NamedArgument(
                arg=flag,
                name=self.words_to_name(
                    choose_unique_name(flag_options, reserved=self.reserved, number=i)
                ),
            )
            for i, (flag, flag_options) in enumerate(zip(flags, options))
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
