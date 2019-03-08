import typing
import abc
import enum
from declivity import cli_types
from dataclasses import dataclass
import re
import math

"""
Contains the CLI data model
"""


@dataclass
class Command:
    def __init__(self, command: typing.List[str], positional: typing.List['Flag'], named: typing.List['Flag']):
        self.command = command
        self.named = []

        # Put the help and usage flag into separate variables
        for flag in named:
            if flag.longest_synonym == '--help' or flag.longest_synonym == '-help':
                self.help_flag = flag
            elif flag.longest_synonym == '--usage':
                self.usage_flag = flag
            else:
                self.named.append(flag)
        self.positional = positional

    positional: typing.List['Flag']
    help_flag: 'Flag'
    usage_flag: 'Flag'
    named: typing.List['Flag']
    command: typing.List[str]


@dataclass
class Flag:
    """
    Represents one single optional flag, with all synonyms for it, and all arguments
    """
    synonyms: typing.List[str]
    description: str
    args: 'FlagArg'

    @staticmethod
    def from_synonyms(synonyms: typing.Iterable['_FlagSynonym'], description: str):
        """
        Creates a useable Flag object by combining the synonyms provided
        """
        synonym_str = []
        args = None
        arg_count = float('-inf')

        for synonym in synonyms:
            synonym_str.append(synonym.name)
            if synonym.argtype.num_args() > arg_count:
                arg_count = synonym.argtype.num_args()
                args = synonym.argtype

        return Flag(
            synonyms=synonym_str,
            args=args,
            description=description
        )

    @staticmethod
    def synonym_to_words(synonym: str) -> typing.Iterable[str]:
        return re.split('[-_]', synonym.lstrip('-'))

    @staticmethod
    def synonym_to_camel(synonym: str) -> str:
        words = Flag.synonym_to_words(synonym)
        return ''.join([segment.capitalize() for segment in words])

    @staticmethod
    def synonym_to_snake(synonym: str) -> str:
        words = Flag.synonym_to_words(synonym)
        return '_'.join([segment for segment in words])

    @property
    def longest_synonym(self) -> str:
        return max(self.synonyms, key=lambda synonym: len(synonym))

    @property
    def shortest_synonym(self) -> str:
        return min(self.synonyms, key=lambda synonym: len(synonym))

    # @staticmethod
    # def tokens_to_name(tokens: typing.List[tokens.Token]):
    #     return re.sub('[^\w]', '', ''.join([tok.text.capitalize() for tok in tokens]))

    # @property
    # def name(self):
    #     """
    #     A short name for this flag
    #     """
    #     no_brackets = re.sub('[[({].+[\])}]', '', self.description)
    #     words = nlp(no_brackets)
    #     # for chunk in words.noun_chunks:
    #     #     if chunk.root.dep_ == 'ROOT':
    #     #         return chunk.text
    #     root = None
    #
    #     # Find the actual root
    #     for word in words:
    #         if (word.dep_ == 'ROOT' or word.dep == 'nsubj') and word.pos_ == 'NOUN':
    #             root = word
    #
    #     # If that isn't there, get the first noun
    #     if root is None:
    #         for word in words:
    #             if word.pos_ == 'NOUN':
    #                 root = word
    #
    #     # If that isn't there, get the first word
    #     if root is None:
    #         return self.tokens_to_name(words)
    #
    #     subtree = list(root.subtree)
    #     if len(subtree) < 4:
    #         # If the whole subtree is a reasonable length, use that
    #         return self.tokens_to_name(subtree)
    #     else:
    #         good_children = [tok for tok in subtree if tok.dep_ != 'prep']
    #         if len(good_children) >= 1:
    #             subtree = sorted([root, good_children[0]], key=lambda tok: tok.i)
    #             # Otherwise, just add the first child token
    #             return self.tokens_to_name(subtree)
    #         else:
    #             return self.tokens_to_name([root])


@dataclass
class _FlagSynonym:
    """
    Internal class for storing the arguments for a single synonym
    """
    name: str
    argtype: 'FlagArg'

    @property
    def capital(self):
        return ''.join([segment.capitalize() for segment in re.split('[-_]', self.name.lstrip('-'))])


@dataclass
class FlagArg(abc.ABC):
    """
    The data model for the argument or arguments for a flag, for example a flag might have no arguments, it might have
    one argument, it might accept one option from a list of options, or it might accept an arbitrary number of inputs
    """
    int_re = re.compile('(int(eger)?)|size|length|max|min', flags=re.IGNORECASE)
    str_re = re.compile('str(ing)?', flags=re.IGNORECASE)
    float_re = re.compile('float|decimal', flags=re.IGNORECASE)
    bool_re = re.compile('bool(ean)?', flags=re.IGNORECASE)
    file_re = re.compile('file', flags=re.IGNORECASE)

    @classmethod
    def infer_type(cls, string) -> cli_types.CliType:
        """
        Reads a string (argument description etc) to find hints about what type this argument might be. This is
        generally called by the get_type() methods
        """
        if cls.bool_re.match(string):
            return cli_types.CliBoolean()
        elif cls.float_re.match(string):
            return cli_types.CliFloat()
        elif cls.int_re.match(string):
            return cli_types.CliInteger()
        elif cls.file_re.match(string):
            return cli_types.CliFile()
        elif cls.str_re.match(string):
            return cli_types.CliString()
        else:
            return cli_types.CliString()

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


@dataclass
class EmptyFlagArg(FlagArg):
    """
    A flag that has no arguments, e.g. `--quiet` that is either present or not present
    """

    def num_args(self) -> int:
        return 0

    def get_type(self):
        return cli_types.CliBoolean()


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
        return cli_types.CliTuple([self.infer_type(arg) for arg in self.names])


@dataclass
class SimpleFlagArg(FlagArg):
    """
    When a flag has one single argument, e.g. `-e PATTERN`, where PATTERN is the argument
    """
    name: str

    def num_args(self) -> int:
        return 1

    def get_type(self):
        return self.infer_type(self.name)


@dataclass
class RepeatFlagArg(FlagArg):
    """
    When a flag accepts 1 or more arguments, e.g. `--samout SAMOUTS [SAMOUTS ...]`
    """
    name: str

    def num_args(self) -> int:
        return 1

    def get_type(self):
        t = self.infer_type(self.name)
        return cli_types.CliList(t)


@dataclass
class ChoiceFlagArg(FlagArg):
    choices: typing.List[str]

    def get_type(self):
        e = enum.Enum(''.join([choice.capitalize() for choice in self.choices]), self.choices)
        return cli_types.CliEnum(e)

    def num_args(self) -> int:
        return 1

