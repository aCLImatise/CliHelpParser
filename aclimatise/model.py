"""
Contains the CLI data model
"""
import abc
import enum
import itertools
import re
import typing
from abc import abstractmethod
from itertools import chain
from operator import attrgetter

import attr
from ruamel.yaml import yaml_object
from word2number import w2n

import aclimatise
from aclimatise import cli_types
from aclimatise.cli_types import CliFileSystemType, CliString
from aclimatise.name_generation import segment_string
from aclimatise.nlp import wordsegment
from aclimatise.usage_parser.model import UsageInstance
from aclimatise.yaml import AttrYamlMixin, yaml


def first(lst: typing.List, default):
    if len(lst) == 0:
        return default
    return lst[0]


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
@attr.s(
    auto_attribs=True,
)
class Command(AttrYamlMixin):
    """
    Class representing an entire command or subcommand, e.g. `bwa mem` or `grep`
    """

    def __attrs_post_init__(self):
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

    def __getitem__(self, item: str) -> "Command":
        """
        If present, returns a subcommand with the following name. For example, samtools_cmd['sort'] will return the
        "samtools sort" command
        """
        for sub in self.subcommands:
            if sub.command == [*self.command, item]:
                return sub
        raise KeyError(
            "{} does not have a subcommand {}".format(" ".join(self.command), item)
        )

    def reanalyse(self, parent: "Command" = None) -> "Command":
        """
        Re-analyses the entire command tree using the existing help text but the current parser, and returns the new tree
        """
        if len(self.subcommands) > 0:
            return Command(
                generated_using=self.generated_using,
                help_text=self.help_text,
                command=self.command,
                subcommands=[cmd.reanalyse(self) for cmd in self.subcommands],
                parent=parent,
            )
        else:
            replacement = aclimatise.parse_help(cmd=self.command, text=self.help_text)
            replacement.parent = parent
            replacement.help_text = self.help_text
            replacement.generated_using = self.generated_using
            return replacement

    def valid_subcommand(self, compare_depth=1) -> bool:
        """
        Returns true if command is a valid subcommand, relative to its parent
        """
        parent = self.ancestor(compare_depth)

        # Recursively call this on all ancestors
        if parent.parent is not None and not self.valid_subcommand(compare_depth + 1):
            return False

        # This isn't a subcommand if it has the same input text as the parent
        if self.help_text and self.help_text == parent.help_text:
            return False

        # This isn't a subcommand if it has no flags
        if len(self.positional) + len(self.named) == 0:
            return False

        # This isn't a subcommand if it shares any positional with the parent command
        for pos_a, pos_b in zip(parent.positional, self.positional):
            if pos_a == pos_b:
                return False

        # This isn't a subcommand if it shares any flags with the parent command
        for flag_a, flag_b in zip(parent.named, self.named):
            if flag_a == flag_b:
                return False

        return True

    @property
    def outputs(self) -> typing.List["CliArgument"]:
        """
        Returns a list of inputs which are also outputs, for example the "-o" flag is normally an input (you have to
        provide a filename), but also an output (you are interested in the contents of the file at that path after the
        command has been run)
        """
        ret = []
        for arg in itertools.chain(self.named, self.positional):
            typ = arg.get_type()
            # Yes this is a bit awkward, the output field should probably be on every type, defaulting to False
            if isinstance(typ, cli_types.CliFileSystemType) and typ.output:
                ret.append(arg)
        return ret

    @property
    def as_filename(self) -> str:
        """
        Returns a sample filename that might be used to store this command (without a suffix)
        """
        return "_".join([token for token in self.command]).replace("-", "_")

    @property
    def empty(self) -> bool:
        """
        True if we think this command failed in parsing, ie it has no arguments
        """
        return (len(self.positional) + len(self.named) + len(self.subcommands)) == 0

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

    def ancestor(self, levels: int = 1) -> typing.Optional["Command"]:
        """
        Returns the ancestor of the command `levels` steps up the family tree. For example, `cmd.ancestor(1)` is
        equivalent to `cmd.parent`. `cmd.ancestor(2)` is equivalent to `cmd.parent.parent`.
        """
        cmd = self
        for i in range(levels):
            cmd = cmd.parent
            if cmd is None:
                break

        return cmd

    @staticmethod
    def best(commands: typing.Collection["Command"]) -> "Command":
        """
        Given a list of commands generated from the same executable, but with different flags, determine the best one
        and return it
        :param commands:
        :return:
        """
        # Currently we just return the command with the most flags
        return max(
            commands,
            key=lambda com: (
                len(com.named) + len(com.positional),
                # len(com.help_text) if com.help_text else 0,
            ),
        )

    @property
    def all_synonyms(self) -> typing.Set[str]:
        """
        Returns all flag synonyms for all flags in this command
        """
        return set(chain.from_iterable([flag.synonyms for flag in self.named]))

    def command_tree(self) -> typing.Generator["Command", None, None]:
        """
        Returns a generator over the entire command tree. e.g. if this command has 2 subcommands, each with 2
            subcommands, this will return a generator with 7 Commands
        """
        yield self
        for command in self.subcommands:
            yield from command.command_tree()

    command: typing.List[str]
    """
    The command line used to invoke this command, e.g. ["bwa", "mem"]
    """

    positional: typing.List["Positional"] = attr.ib(factory=list)
    """
    All positional arguments supported by this command
    """

    named: typing.List["Flag"] = attr.ib(factory=list)
    """
    All named arguments (flags) supported by this command
    """

    parent: typing.Optional["Command"] = None
    """
    The parent command, if this is a subcommand
    """

    subcommands: typing.List["Command"] = attr.ib(factory=list)
    """
    A list of subcommands of this command, e.g. "bwa" has the subcommand "bwa mem"
    """

    usage: typing.List["UsageInstance"] = attr.ib(factory=list)
    """
    Different usage examples provided by the help
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

    docker_image: typing.Optional[str] = None
    """
    If available, a docker image in which to run this command
    """


@yaml_object(yaml)
@attr.s(auto_attribs=True)
class CliArgument(AttrYamlMixin):
    """
    A generic parent class for both named and positional CLI arguments
    """

    description: str
    """
    Description of the function of this argument
    """

    optional: bool = False
    """
    If true, this argument is not required
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
@attr.s(auto_attribs=True, kw_only=True)
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

    @staticmethod
    def deduplicate(
        positionals: typing.Collection["Positional"],
    ) -> typing.List["Positional"]:
        key = attrgetter("name")
        sort = sorted(positionals, key=key)
        groups = itertools.groupby(sort, key=key)
        ret = []
        for key, group in groups:
            grp = list(group)
            ret.append(Positional.merge(grp))
        return sorted(ret, key=attrgetter("position"))

    @staticmethod
    def merge(other: typing.List["Positional"]) -> "Positional":
        """
        Combine the information contained within two Positionals, and return the new Positional
        """
        return Positional(
            position=first(
                [pos.position for pos in other if pos.position is not None], -1
            ),
            name=first(
                [
                    pos.name
                    for pos in other
                    if pos.name is not None and len(pos.name) > 0
                ],
                None,
            ),
            # We want this to be optional if it is considered optional in any situation
            optional=any([pos.optional for pos in other]),
            description=max([pos.description for pos in other], key=len, default=None),
        )

    def get_type(self) -> cli_types.CliType:
        # Try the the flag name, then the description in that order

        name_type = infer_type(self.name)
        if name_type is not None:
            return name_type

        return infer_type(self.full_name()) or cli_types.CliString()


@yaml_object(yaml)
@attr.s(auto_attribs=True, kw_only=True)
class Flag(CliArgument):
    """
    Represents one single flag, with all synonyms for it, and all arguments, e.g. `-h, --help`
    """

    optional: bool = True
    """
    If true, this argument is not required
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

    def __attrs_post_init__(self):
        if self.optional is None:
            # Flags are optional by default
            self.optional = True

    @staticmethod
    def deduplicate(flags: typing.Collection["Flag"]) -> typing.List["Flag"]:
        todo = list(flags[:])
        clusters = []

        while len(todo) > 0:
            # Choose a flag, then find anything it intersects with
            flag_i = todo.pop()
            current_cluster = [flag_i]
            current_synonyms = set(flag_i.synonyms)
            to_remove = []

            for j in range(len(todo)):
                flag_j = todo[j]
                if set(flag_j.synonyms).intersection(current_synonyms):
                    to_remove.append(j)
                    current_synonyms.update(flag_j.synonyms)
                    current_cluster.append(flag_j)

            clusters.append(current_cluster)

        return [Flag.merge(cluster) for cluster in clusters]

    @staticmethod
    def merge(flags: typing.List["Flag"]) -> "Flag":
        """
        Combine the information contained within two Flags, and return the new Flag
        """
        return Flag(
            # Take the longest description
            description=max([flag.description for flag in flags], key=len),
            # Just union the two lists
            synonyms=list(set().union(*[flag.synonyms for flag in flags])),
            args=first([flag.args for flag in flags if flag.args], EmptyFlagArg()),
            optional=any([flag.optional for flag in flags]),
        )

    @staticmethod
    def combine(
        flag_lists: typing.Iterable[typing.Iterable["Flag"]],
    ) -> typing.Iterable["Flag"]:
        """
        Combines the flags from several sources, choosing the first one preferentially
        """
        lookup = {}

        # Build a list of flags, but only ever choose the first instance of a synonym
        for flags in flag_lists:
            for flag in flags:
                for synonym in flag.synonyms:
                    stripped = synonym.lstrip("-")
                    if stripped not in lookup:
                        lookup[stripped] = flag

        # Now, make them unique by description
        unique = {flag.longest_synonym: flag for flag in lookup.values()}

        return list(unique.values())

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
        flag_type = infer_type(self.full_name())
        desc_type = infer_type(self.description)

        candidates = [
            cand
            for cand in [
                arg_type,
                flag_type,
                desc_type,
            ]
            if cand is not None
        ]
        if len(candidates) == 0:
            return CliString()

        # TODO: make this sorting a bit better using CliType.representable
        prioritised = sorted(
            candidates,
            key=lambda typ: (
                not isinstance(typ, CliString),  # First, prioritise non-strings,
                isinstance(typ, CliFileSystemType)
                and typ.output,  # Next, prioritise output types
            ),
            reverse=True,
        )

        return prioritised[0]

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
@attr.s(auto_attribs=True)
class FlagSynonym(AttrYamlMixin):
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


int_re = re.compile(
    r"\b((int(eger)?)|size|length|max|min|(num(ber)?))\b", flags=re.IGNORECASE
)
str_re = re.compile(r"\bstr(ing)?\b", flags=re.IGNORECASE)
float_re = re.compile(r"\b(float|decimal)\b", flags=re.IGNORECASE)
bool_re = re.compile(r"\bbool(ean)?\b", flags=re.IGNORECASE)
file_re = re.compile(r"\b(file(name|path)?|path)\b", flags=re.IGNORECASE)
input_re = re.compile(r"input", flags=re.IGNORECASE)
output_re = re.compile(r"\bout(put)?\b", flags=re.IGNORECASE)
dir_re = re.compile(r"\b(folder|directory)\b", flags=re.IGNORECASE)

float_num_re = re.compile(
    r"[+-]?(([0-9]*\.[0-9]+)|((?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)))",
    flags=re.IGNORECASE,
)
int_num_re = re.compile(r"([+-]?[0-9]+)", flags=re.IGNORECASE)


def distinguish_inout(
    string, cls: typing.Type[cli_types.CliFileSystemType]
) -> cli_types.CliFileSystemType:
    """
    distinguish input/output files/directories given a string
    """
    im = input_re.search(string)
    om = output_re.search(string)
    if not im and om:
        return cls(output=True)
    else:
        return cls(output=False)


def infer_type(string) -> typing.Optional[cli_types.CliType]:
    """
    Reads a string (argument description etc) to find hints about what type this argument might be. This is
    generally called by the get_type() methods
    """
    if bool_re.search(string):
        return cli_types.CliBoolean()
    elif float_re.search(string):
        return cli_types.CliFloat()
    elif int_re.search(string):
        return cli_types.CliInteger()
    elif file_re.search(string):
        return distinguish_inout(string, cli_types.CliFile)
    elif dir_re.search(string):
        return distinguish_inout(string, cli_types.CliDir)
    elif str_re.search(string):
        return cli_types.CliString()
    elif float_num_re.search(string):
        return cli_types.CliFloat()
    elif int_num_re.search(string):
        return cli_types.CliInteger()
    else:
        return None


@yaml_object(yaml)
@attr.s(auto_attribs=True)
class FlagArg(abc.ABC, AttrYamlMixin):
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
@attr.s(auto_attribs=True)
class EmptyFlagArg(FlagArg):
    """
    A flag that has no arguments, e.g. `--quiet` that is either present or not present
    """

    def num_args(self) -> int:
        return 0

    def get_type(self):
        return cli_types.CliBoolean()


@yaml_object(yaml)
@attr.s(auto_attribs=True)
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
        return cli_types.CliTuple(
            [infer_type(" ".join(wordsegment.segment(arg))) for arg in self.names]
        )


@yaml_object(yaml)
@attr.s(auto_attribs=True)
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
        return infer_type(" ".join(wordsegment.segment(self.name))) or None


@yaml_object(yaml)
@attr.s(auto_attribs=True)
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
        t = (
            infer_type(" ".join(wordsegment.segment(self.name)))
            or cli_types.CliString()
        )
        return cli_types.CliList(t)


@yaml_object(yaml)
@attr.s(auto_attribs=True)
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
