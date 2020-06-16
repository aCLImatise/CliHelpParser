"""
Contains the CLI data model
"""
import abc
import enum
import itertools
import re
import typing
import unicodedata
from abc import abstractmethod

import spacy
from dataclasses import InitVar, dataclass, field
from ruamel.yaml import YAML, yaml_object
from spacy import tokens
from word2number import w2n

from acclimatise import cli_types
from acclimatise.name_generation import generate_name, segment_string
from acclimatise.nlp import wordsegment
from acclimatise.yaml import yaml


def useless_name(name: typing.List[str]):
    """
    Returns true if this name (sequence of strings) shouldn't be used as a variable name because it's too short and
    uninformative. This includes an entirely numeric name, which is almost never what you want
    """
    joined = "".join(name)
    if len(name) < 1 or len(joined) <= 1 or joined.isnumeric():
        return True

    # Numeric names are not useful
    try:
        if all([w2n.word_to_num(tok) is not None for tok in name]):
            return True
    except Exception:
        pass

    return False


@yaml_object(yaml)
@dataclass
class Command:
    """
    Class representing an entire command or subcommand, e.g. `bwa mem` or `grep`
    """

    def __post_init__(self):
        # Store certain special flags in their own fields
        if self.help_flag is None:
            for flag in self.named:
                if (
                    "--help" in flag.synonyms
                    or "-help" in flag.synonyms
                    or ("-h" in flag.synonyms and isinstance(flag.args, EmptyFlagArg))
                ):
                    self.help_flag = flag
                    self.named.remove(flag)

        if self.version_flag is None:
            for flag in self.named:
                if "--version" in flag.synonyms:
                    self.version_flag = flag
                    self.named.remove(flag)

        if self.usage_flag is None:
            for flag in self.named:
                if "--usage" in flag.synonyms:
                    self.usage_flag = flag
                    self.named.remove(flag)

    @property
    def as_filename(self) -> str:
        """
        Returns a sample filename that might be used to store this command (without a suffix)
        """
        return "_".join(self.command).replace("-", "_")

    @property
    def depth(self) -> int:
        """
        Returns the "depth" of this command, aka how many ancestors it has. An orphan command has depth 0, a subcommand
        has depth 1, a sub-sub-command has depth 2 etc
        """
        cmd = self
        depth = 0
        while cmd.parent is not None:
            cmd = cmd.parent
            depth += 1

        return depth

    def command_tree(self) -> typing.Generator["Command", None, None]:
        """
        Returns a generator over the entire command tree. e.g. if this command has 2 subcommands, each with 2
            subcommands, this will return a generator with 7 Commands
        """
        yield self
        for command in self.subcommands:
            yield from command.command_tree()

    positional: typing.List["Positional"]
    """
    All positional arguments supported by this command
    """

    named: typing.List["Flag"]
    """
    All named arguments (flags) supported by this command
    """

    command: typing.List[str]
    """
    The command line used to invoke this command, e.g. ["bwa", "mem"]
    """

    parent: typing.Optional["Command"] = None
    """
    The parent command, if this is a subcommand
    """

    subcommands: typing.List["Command"] = field(default_factory=list)
    """
    A list of subcommands of this command, e.g. "bwa" has the subcommand "bwa mem"
    """

    help_flag: typing.Optional["Flag"] = None
    """
    If identified, this is the flag that returns help text
    """

    usage_flag: typing.Optional["Flag"] = None
    """
    If identified, this is the flag that returns usage examples
    """

    version_flag: typing.Optional["Flag"] = None
    """
    If identified, this is the flag that returns the version of the executable
    """

    help_text: typing.Optional[str] = None
    """
    Optionally, the entire help text that was used to generate this Command
    """

    generated_using: typing.Optional[str] = None
    """
    Optionally, the flag that was used to generate this command. Often this will be the same as the help_flag
    """


@yaml_object(yaml)
@dataclass(unsafe_hash=True)
class CliArgument:
    """
    A generic parent class for both named and positional CLI arguments
    """

    description: str
    """
    Description of the function of this argument
    """

    @abstractmethod
    def argument_name(self) -> typing.List[str]:
        return []

    @abstractmethod
    def full_name(self) -> str:
        """
        Return a human-readable representation of this argument
        """
        pass

    @abstractmethod
    def get_type(self) -> cli_types.CliType:
        """
        Return a type object indicating the type of data this argument holds. e.g. If it's an array type this will be a
        CliList.
        """
        pass


@yaml_object(yaml)
@dataclass
class Positional(CliArgument):
    """
    A positional command-line argument. This probably means that it is required, and has no arguments like flags do
    """

    def full_name(self) -> str:
        """
        Getting the full name for a positional argument is easy - it's just the parameter name
        """
        return self.name

    position: int
    """
    The position in the command line that this argument must occupy
    """

    name: str
    """
    The name of this argument
    """

    description: str
    """
    A description of the function of this argument
    """

    optional: bool = False
    """
    If true, this argument is not required
    """

    def get_type(self) -> cli_types.CliType:
        # Try the the flag name, then the description in that order

        name_type = infer_type(self.name)
        if name_type is not None:
            return name_type

        flag_type = infer_type(self.full_name())
        if flag_type is not None:
            return flag_type

        return cli_types.CliString()


@yaml_object(yaml)
@dataclass(unsafe_hash=True)
class Flag(CliArgument):
    """
    Represents one single flag, with all synonyms for it, and all arguments, e.g. `-h, --help`
    """

    synonyms: typing.List[str]
    """
    A list of different ways to invoke this same option, e.g. ``-v`` and ``--verbose``
    """

    description: typing.Optional[str]
    """
    A description of the function of this flag
    """

    args: "FlagArg"
    """
    Describes the arguments to this flag, e.g. ``-n 1`` has a single numeric argument
    """

    optional: bool = True
    """
    If true, this flag is not required (the default)
    """

    def argument_text(self) -> typing.List[str]:
        return self.args.text()

    def variable_name(
        self, description_name: typing.List[str] = []
    ) -> typing.List[str]:
        """
        Returns a list of words that should be used in a variable name for this argument
        """
        # The super method returns the best name from the flag name or the description. If neither is sufficient, use
        # the argument to generate a name
        best = super().variable_name(description_name)

        if useless_name(best):
            nfa = list(self._name_from_arg)
            if not useless_name(nfa):
                return nfa

        return best

    @property
    def _name_from_arg(self) -> typing.Iterable[str]:
        """
        Generate a 1-3 word variable name for this flag, by parsing the description
        """
        if self.args is not None and hasattr(self.args, "name"):
            return segment_string(self.args.name)
        else:
            return []

    def get_type(self) -> cli_types.CliType:
        # Try the argument name, then the flag name, then the description in that order
        arg_type = self.args.get_type()
        if arg_type is not None:
            return arg_type

        flag_type = infer_type(self.full_name())
        if flag_type is not None:
            return flag_type

        description_type = infer_type(self.description)
        if description_type is not None:
            return description_type

        return cli_types.CliString()

    def full_name(self) -> str:
        """
        Getting the full name for a named flag is slightly harder, we need to find the longest synonym
        """
        return self.longest_synonym

    @staticmethod
    def from_synonyms(
        synonyms: typing.Iterable["FlagSynonym"], description: typing.Optional[str]
    ):
        """
        Creates a usable Flag object by combining the synonyms provided
        """
        synonym_str = []
        args = None
        arg_count = float("-inf")

        for synonym in synonyms:
            synonym_str.append(synonym.name)
            if synonym.argtype.num_args() > arg_count:
                arg_count = synonym.argtype.num_args()
                args = synonym.argtype

        return Flag(synonyms=synonym_str, args=args, description=description)

    @property
    def longest_synonym(self) -> str:
        """
        Returns the longest synonym this flag has. e.g. for `-h, --help`, it will return `--help`
        """
        return max(self.synonyms, key=lambda synonym: len(synonym))

    @property
    def shortest_synonym(self) -> str:
        """
        Returns the shortest synonym this flag has. e.g. for `-h, --help`, it will return `-h`
        """
        return min(self.synonyms, key=lambda synonym: len(synonym))


@yaml_object(yaml)
@dataclass
class FlagSynonym:
    """
    Internal class for storing the arguments for a single synonym
    """

    name: str
    """
    The entire flag string, e.g. "-n" or "--lines"
    """

    argtype: "FlagArg"
    """
    The number and type of arguments that this flag takes
    """

    @property
    def capital(self):
        return "".join(
            [
                segment.capitalize()
                for segment in re.split("[-_]", self.name.lstrip("-"))
            ]
        )


int_re = re.compile("(int(eger)?)|size|length|max|min", flags=re.IGNORECASE)
str_re = re.compile("str(ing)?", flags=re.IGNORECASE)
float_re = re.compile("float|decimal", flags=re.IGNORECASE)
bool_re = re.compile("bool(ean)?", flags=re.IGNORECASE)
file_re = re.compile("file|path", flags=re.IGNORECASE)
dir_re = re.compile("folder|directory", flags=re.IGNORECASE)


def infer_type(string) -> typing.Optional[cli_types.CliType]:
    """
    Reads a string (argument description etc) to find hints about what type this argument might be. This is
    generally called by the get_type() methods
    """
    if bool_re.match(string):
        return cli_types.CliBoolean()
    elif float_re.match(string):
        return cli_types.CliFloat()
    elif int_re.match(string):
        return cli_types.CliInteger()
    elif file_re.match(string):
        return cli_types.CliFile()
    elif dir_re.match(string):
        return cli_types.CliDir()
    elif str_re.match(string):
        return cli_types.CliString()
    else:
        return cli_types.CliString()


@yaml_object(yaml)
@dataclass
class FlagArg(abc.ABC):
    """
    The data model for the argument or arguments for a flag, for example a flag might have no arguments, it might have
    one argument, it might accept one option from a list of options, or it might accept an arbitrary number of inputs
    """

    def text(self) -> typing.List[str]:
        """
        Returns the text of the argument, e.g. for name generation purposes
        """
        return []

    @abc.abstractmethod
    def get_type(self) -> cli_types.CliType:
        """
        Return a type object indicating the type of data this argument holds. e.g. If it's an array type this will be a
        CliList.
        """
        pass

    @abc.abstractmethod
    def num_args(self) -> int:
        """
        Calculate the multiplicity of this argument
        """
        pass


@yaml_object(yaml)
@dataclass
class EmptyFlagArg(FlagArg):
    """
    A flag that has no arguments, e.g. `--quiet` that is either present or not present
    """

    def num_args(self) -> int:
        return 0

    def get_type(self):
        return cli_types.CliBoolean()


@yaml_object(yaml)
@dataclass
class OptionalFlagArg(FlagArg):
    """
    When the flag has multiple arguments, some of which are optional, e.g.
    -I FLOAT[,FLOAT[,INT[,INT]]]
    """

    names: list
    """
    Names of each argument
    """

    separator: str
    """
    Separator between each argument
    """

    def text(self) -> typing.List[str]:
        return list(
            itertools.chain.from_iterable(
                [wordsegment.segment(name) for name in self.names]
            )
        )

    def num_args(self) -> int:
        return len(self.names)

    def get_type(self):
        return cli_types.CliTuple([infer_type(arg) for arg in self.names])


@yaml_object(yaml)
@dataclass
class SimpleFlagArg(FlagArg):
    """
    When a flag has one single argument, e.g. `-e PATTERN`, where PATTERN is the argument
    """

    name: str
    """
    Name of this argument
    """

    def text(self) -> typing.List[str]:
        return list(wordsegment.segment(self.name))

    def num_args(self) -> int:
        return 1

    def get_type(self):
        return infer_type(self.name)


@yaml_object(yaml)
@dataclass
class RepeatFlagArg(FlagArg):
    """
    When a flag accepts 1 or more arguments, e.g. `--samout SAMOUTS [SAMOUTS ...]`
    """

    name: str
    """
    The name of this argument
    """

    def text(self) -> typing.List[str]:
        return list(wordsegment.segment(self.name))

    def num_args(self) -> int:
        return 1

    def get_type(self):
        t = infer_type(self.name)
        return cli_types.CliList(t)


@yaml_object(yaml)
@dataclass
class ChoiceFlagArg(FlagArg):
    """
    When a flag accepts one option from a list of options, e.g. `-s {yes,no,reverse}`
    """

    choices: typing.Set[str]
    """
    Set of possible choices that could be used for this argument
    """

    def text(self) -> typing.List[str]:
        return list(
            itertools.chain.from_iterable(
                [wordsegment.segment(name) for name in self.choices]
            )
        )

    def get_type(self):
        e = enum.Enum(
            "".join([choice.capitalize() for choice in self.choices]),
            list(self.choices),
        )
        return cli_types.CliEnum(e)

    def num_args(self) -> int:
        return 1
