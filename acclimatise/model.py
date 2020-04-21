"""
Contains the CLI data model
"""
import abc
import enum
import itertools
import re
import typing
from abc import abstractmethod
from dataclasses import InitVar, dataclass, field

import spacy
import wordsegment
from acclimatise import cli_types
from acclimatise.yaml import yaml
from ruamel.yaml import YAML, yaml_object
from spacy import tokens


@yaml_object(yaml)
@dataclass
class CliArgument:
    """
    A generic parent class for both named and positional CLI arguments
    """

    #: Description of the function of this argument
    description: str

    #: Whether the existence of this argument is supported by it appearing in the usage
    usage_supported: bool = field(default=False, init=False)

    @staticmethod
    def tokens_to_name(tokens: typing.List[tokens.Token]):
        return re.sub("[^\w]", "", "".join([tok.text.capitalize() for tok in tokens]))

    @abstractmethod
    def full_name(self) -> str:
        pass

    @abstractmethod
    def get_type(self) -> cli_types.CliType:
        """
        Return a type object indicating the type of data this argument holds. e.g. If it's an array type this will be a CliList.
        """
        pass

    def name_to_words(self) -> typing.Iterable[str]:
        """
        Splits this argument's name into multiple words
        """
        # Load wordsegment the first time
        if len(wordsegment.WORDS) == 0:
            wordsegment.load()

        dash_tokens = re.split("[-_]", self.full_name().lstrip("-"))
        segment_tokens = itertools.chain.from_iterable(
            [wordsegment.segment(w) for w in dash_tokens]
        )
        return segment_tokens

    def name_to_camel(self) -> str:
        """
        Gets a representation of this argument in CamelCase
        """
        words = list(self.name_to_words())
        cased = [words[0].lower()] + [segment.capitalize() for segment in words]
        return "".join(cased)

    def name_to_snake(self) -> str:
        """
        Gets a representation of this argument in snake case
        """
        words = self.name_to_words()
        return "_".join([segment for segment in words])

    def generate_name(self) -> str:
        """
        Generate a 1-3 word variable name for this flag, by parsing the description
        """
        try:
            nlp = spacy.load("en")
        except IOError:
            nlp = None

        if nlp is None:
            raise Exception(
                "Spacy model doesn't exist! Install it with `python -m spacy download en`"
            )

        no_brackets = re.sub("[\[({].+[\])}]", "", self.description)
        words = nlp(no_brackets)
        # for chunk in words.noun_chunks:
        #     if chunk.root.dep_ == 'ROOT':
        #         return chunk.text
        root = None

        # Find the actual root
        for word in words:
            if (word.dep_ == "ROOT" or word.dep == "nsubj") and word.pos_ == "NOUN":
                root = word

        # If that isn't there, get the first noun
        if root is None:
            for word in words:
                if word.pos_ == "NOUN":
                    root = word

        # If that isn't there, get the first word
        if root is None:
            return self.tokens_to_name(words)

        subtree = list(root.subtree)
        if len(subtree) < 4:
            # If the whole subtree is a reasonable length, use that
            return self.tokens_to_name(subtree)
        else:
            good_children = [tok for tok in subtree if tok.dep_ != "prep"]
            if len(good_children) >= 1:
                subtree = sorted([root, good_children[0]], key=lambda tok: tok.i)
                # Otherwise, just add the first child token
                return self.tokens_to_name(subtree)
            else:
                return self.tokens_to_name([root])


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

    #
    # def __init__(
    #     self,
    #     command: typing.List[str],
    #     positional: typing.List["Positional"],
    #     named: typing.List["Flag"],
    #     **kwargs
    # ):
    #     super().__init__(**kwargs)
    #
    #     self.command = command
    #     self.named = []
    #
    #     # Put the help and usage flag into separate variables
    #     for flag in named:
    #         if (
    #             "--help" in flag.synonyms
    #             or "-help" in flag.synonyms
    #             or ("-h" in flag.synonyms and isinstance(flag.args, EmptyFlagArg))
    #         ):
    #             self.help_flag = flag
    #         elif "--usage" in flag.synonyms:
    #             self.usage_flag = flag
    #         elif "--version" in flag.synonyms:  # or "-v" in flag.synonyms:
    #             self.version_flag = flag
    #         else:
    #             self.named.append(flag)
    #     self.positional = positional

    positional: typing.List["Positional"]
    named: typing.List["Flag"]
    command: typing.List[str]

    subcommands: typing.List["Command"] = field(default_factory=list)
    help_flag: typing.Optional["Flag"] = None
    usage_flag: typing.Optional["Flag"] = None
    version_flag: typing.Optional["Flag"] = None


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
    name: str
    description: str
    optional: bool = False

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
@dataclass
class Flag(CliArgument):
    """
    Represents one single flag, with all synonyms for it, and all arguments, e.g. `-h, --help`
    """

    synonyms: typing.List[str]
    description: typing.Optional[str]
    args: "FlagArg"
    optional: bool = True

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

    choices: typing.List[str]

    def get_type(self):
        e = enum.Enum(
            "".join([choice.capitalize() for choice in self.choices]), self.choices
        )
        return cli_types.CliEnum(e)

    def num_args(self) -> int:
        return 1
