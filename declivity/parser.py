from pyparsing import Literal, Regex, indentedBlock, And, Word, alphanums, Or, OneOrMore, originalTextFor, SkipTo, \
    tokenMap, LineEnd, White, Optional, delimitedList, matchPreviousLiteral, nestedExpr, alphas, Forward
from dataclasses import dataclass
import re
import typing
import abc
import enum
from declivity import types
import spacy
from spacy import displacy, tokens

nlp = spacy.load('en_core_web_sm')


def pick(*args):
    def action(s, loc, toks):
        if len(args) == 1:
            return toks[args[0]]
        else:
            return [toks[arg] for arg in args]

    return action


@dataclass
class Command:
    flags: typing.List['Flag']
    command: typing.List[str]


@dataclass
class Flag:
    synonyms: typing.List['FlagName']
    description: str

    @property
    def args(self) -> 'FlagName':
        return max(self.synonyms, key=lambda synonym: synonym.argtype.num_args)

    @property
    def longest_synonym(self) -> 'FlagName':
        return max(self.synonyms, key=lambda synonym: len(synonym.name))

    def shortest_synonym(self) -> 'FlagName':
        return min(self.synonyms, key=lambda synonym: len(synonym.name))

    def tokens_to_name(self, tokens: typing.List[tokens.Token]):
        return re.sub('[^\w]', '', ''.join([tok.text.capitalize() for tok in tokens]))

    @property
    def name(self):
        """
        A short name for this flag
        """
        no_brackets = re.sub('[[({].+[\])}]', '', self.description)
        words = nlp(no_brackets)
        # for chunk in words.noun_chunks:
        #     if chunk.root.dep_ == 'ROOT':
        #         return chunk.text
        root = None

        # Find the actual root
        for word in words:
            if (word.dep_ == 'ROOT' or word.dep == 'nsubj') and word.pos_ == 'NOUN':
                root = word

        # If that isn't there, get the first noun
        if root is None:
            for word in words:
                if word.pos_ == 'NOUN':
                    root = word

        # If that isn't there, get the first word
        if root is None:
            return self.tokens_to_name(words)

        subtree = list(root.subtree)
        if len(subtree) < 4:
            # If the whole subtree is a reasonable length, use that
            return self.tokens_to_name(subtree)
        else:
            good_children = [tok for tok in subtree if tok.dep_ != 'prep']
            if len(good_children) >= 1:
                subtree = sorted([root, good_children[0]], key=lambda tok: tok.i)
                # Otherwise, just add the first child token
                return self.tokens_to_name(subtree)
            else:
                return self.tokens_to_name([root])


@dataclass
class FlagName:
    name: str
    argtype: 'FlagArg'


@dataclass
class FlagArg(abc.ABC):
    int_re = re.compile('int(eger)?', flags=re.IGNORECASE)
    str_re = re.compile('str(ing)?', flags=re.IGNORECASE)
    float_re = re.compile('float|decimal', flags=re.IGNORECASE)
    bool_re = re.compile('bool(ean)?', flags=re.IGNORECASE)
    file_re = re.compile('file', flags=re.IGNORECASE)

    @classmethod
    def infer_type(cls, string) -> types.CliType:
        if cls.bool_re.match(string):
            return types.CliBoolean()
        elif cls.float_re.match(string):
            return types.CliFloat()
        elif cls.int_re.match(string):
            return types.CliInteger()
        elif cls.file_re.match(string):
            return types.CliFile()
        elif cls.str_re.match(string):
            return types.CliString()
        else:
            return types.CliString()

    @abc.abstractmethod
    def get_type(self) -> types.CliType:
        pass

    @abc.abstractmethod
    def num_args(self) -> int:
        pass


@dataclass
class EmptyFlagArg(FlagArg):

    def num_args(self) -> int:
        return 0

    def get_type(self):
        return types.CliBoolean


@dataclass
class OptionalFlagArg(FlagArg):
    """
    When the flag has multiple arguments, some of which are optional, e.g.
    -I FLOAT[,FLOAT[,INT[,INT]]]
    """

    def num_args(self) -> int:
        return len(self.args)

    args: list

    def get_type(self):
        return types.CliTuple([self.infer_type(arg) for arg in self.args])


@dataclass
class SimpleFlagArg(FlagArg):
    def num_args(self) -> int:
        return 1

    def get_type(self):
        return self.infer_type(self.arg)

    arg: str


@dataclass
class RepeatFlagArg(FlagArg):
    def num_args(self) -> int:
        return 1

    def get_type(self):
        t = self.infer_type(self.arg)
        return typing.List[t]

    arg: str


@dataclass
class ChoiceFlagArg(FlagArg):
    def get_type(self):
        return enum.Enum(value=','.join(self.choices), names=self.choices)

    def num_args(self) -> int:
        return 1

    choices: typing.List[str]


class CliParser:
    def parse_command(self, cmd, name):
        flag_block = list(self.flags.searchString(cmd))
        flags = [flag[0] for flags in flag_block for flag in flags]
        return Command(
            command=name,
            flags=flags
        )

    def __init__(self):
        stack = [1]
        self.cli_id = Word(initChars=alphas, bodyChars=alphanums + '-_')

        self.short_flag = originalTextFor(Literal('-') + Word(alphanums, max=1))
        """A short flag has only a single dash and single character, e.g. `-m`"""
        self.long_flag = originalTextFor(Literal('--') + self.cli_id)
        """A long flag has two dashes and any amount of characters, e.g. `--max-count`"""
        self.any_flag = self.short_flag ^ self.long_flag
        """The flag is the part with the dashes, e.g. `-m` or `--max-count`"""

        self.flag_arg_sep = Or([Literal('='), Literal(' ')]).leaveWhitespace()
        """The term that separates the flag from the arguments, e.g. in `--file=FILE` it's `=`"""

        self.arg_arg_sep = Or([Literal('='), Literal(' ')]).leaveWhitespace()
        """The term that separates arguments from each other, e.g. in `--file=FILE` it's `=`"""

        self.arg = self.cli_id.copy()
        """A single argument name, e.g. `FILE`"""

        def visit_optional_args(s, lok, toks):
            if len(toks) == 1:
                return OptionalFlagArg(args=[toks[0]])
            else:
                other = toks[3]
                if isinstance(other, str):
                    return OptionalFlagArg(args=[toks[0], other])
                elif isinstance(other, OptionalFlagArg):
                    return OptionalFlagArg(args=[toks[0]] + other.args)

        self.optional_args = Forward()
        self.optional_args <<= (
                self.arg
                + Literal('[') + Literal(',') + (self.optional_args ^ self.arg) + Literal(']')
        ).setParseAction(visit_optional_args)
        """
        When the flag has multiple arguments, some of which are optional, e.g.
        -I FLOAT[,FLOAT[,INT[,INT]]]
        """

        self.simple_arg = self.arg.copy().setParseAction(lambda s, loc, toks: SimpleFlagArg(toks[0]))

        self.list_type_arg = (
                self.arg
                + Literal('[')
                + matchPreviousLiteral(self.arg)
                + Literal('...')
                + Literal(']')
        ).setParseAction(lambda s, loc, toks: RepeatFlagArg(toks[0]))
        """When the argument is an array of values, e.g. when the help says `--samout SAMOUTS [SAMOUTS ...]`"""

        self.choice_type_arg = nestedExpr(
            opener='{',
            closer='}',
            content=delimitedList(self.cli_id, delim=',')
        ).setParseAction(lambda s, loc, toks: ChoiceFlagArg(toks[0]))
        """When the argument is one from a list of values, e.g. when the help says `--format {sam,bam}`"""

        self.arg_expression = (
                self.flag_arg_sep.suppress() + (
                self.list_type_arg ^ self.choice_type_arg ^ self.optional_args ^ self.simple_arg)
        ).setParseAction(
            lambda s, loc, toks: toks[0])
        """An argument with separator, e.g. `=FILE`"""

        self.flag_with_arg = (self.any_flag + Optional(self.arg_expression)).setParseAction(
            lambda s, loc, toks: (
                FlagName(name=toks[0], argtype=toks[1] if len(toks) > 1 else EmptyFlagArg())
            )
        )
        """e.g. `--max-count=NUM`"""

        self.flag_synonyms = delimitedList(self.flag_with_arg, delim=Literal(' ') ^ Literal(','))
        """
        When the help lists multiple synonyms for a flag, e.g:
        -n, --lines=NUM
        """

        # The description of the flag
        # e.g. for grep's `-o, --only-matching`, this is:
        # "Print only the matched (non-empty) parts of a matching line, with each such part on a separate output line."
        def success(a, b, c):
            pass

        self.desc_line = originalTextFor(SkipTo(LineEnd()))  # .setParseAction(success))
        self.indented_desc = indentedBlock(
            self.desc_line,
            indentStack=stack,
            indent=True
        ).setParseAction(
            lambda s, loc, toks: ' '.join([tok[0] for tok in toks[0]])
        )
        self.description = self.indented_desc  # Optional(one_line_desc) + Optional(self.indented_desc)
        # A self.description that takes up one line
        # one_line_desc = SkipTo(LineEnd())

        # A flag self.description that makes up an indented block
        # originalTextFor(SkipTo(flag_prefix ^ LineEnd()))

        # The entire flag documentation, including all synonyms and description
        self.flag = (
                self.flag_synonyms
                + self.description
        ).setParseAction(
            lambda s, loc, toks:
            (
                Flag(
                    synonyms=toks[0:-1],
                    description=toks[-1]
                )
            )
        )

        def visit_flags(s, loc, toks):
            return toks[0]

        self.flags = indentedBlock(self.flag, indentStack=stack, indent=True).setParseAction(visit_flags)
        self.flag_section_header = Regex('(arguments|options):', flags=re.IGNORECASE)
        self.flag_section = (self.flag_section_header + self.flags).setParseAction(lambda s, loc, toks: toks[1:])
