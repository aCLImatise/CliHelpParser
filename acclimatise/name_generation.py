import itertools
import unicodedata
from collections import Counter, defaultdict
from itertools import groupby
from typing import Generator, Iterable, List, Optional, Set

from spacy.tokens import Token

import regex as re
from acclimatise.nlp import nlp, wordsegment


def duplicate_keys(l: list) -> Set[int]:
    """
    Identifies the indexes of duplicates in a given list
    """
    ret = set()
    for entry, indices in groupby(
        sorted(enumerate(l), key=lambda x: x[1]), key=lambda x: x[1]
    ):
        indices = list(indices)
        if len(indices) > 1 and len("".join(entry)) > 0:
            # The keys we still need to iterate on are those with duplicate commands, but if the names are empty
            # strings, we should stop iterating and try another method
            for index in indices:
                ret.add(index[0])
    return ret


def sanitize_symbols(text):
    """
    Remove any non-word symbols
    """
    return re.sub("[^[:alpha:]-_., ]", "", text)


def sanitize_token(text):
    """
    Remove any non-word symbols
    """
    return re.sub("[^[:alpha:]]", "", text)


def replace_hyphens(text):
    """
    Remove any non-word symbols
    """
    return re.sub("-", "_", text)


def should_ignore(token):
    return token.pos_ not in {"NOUN", "NUM", "PRON", "PROPN", "VERB"}


def distance_to_root(token, root):
    if token == root:
        return 0
    else:
        dist = 0
        while token != root:
            dist += 1
            token = token.head
        return dist


def token_priority(token: Token, current: List[Token]) -> int:
    """
    Returns a priority (where lowest means highest priority) of tokens
    :param token: The token to prioritise
    :param current: The current list of tokens in the name
    """
    if token.pos_ not in {"NOUN", "NUM", "PRON", "PROPN", "VERB", "ADJ", "ADV"}:
        return 1000 + token.idx
    else:
        if token.dep_ != "HEAD" and token.head not in current:
            # If this is, say, an adjective but the noun it's attached to isn't in the list, massively penalise this
            return 500 + token.idx
        else:
            return token.idx
    # if should_ignore(token):
    #     return 100 + distance_to_root(token, root)
    # else:
    #     return distance_to_root(token, root)


def remove_delims(text):
    for delims in (("\\[", "\\]"), ("{", "}"), ("'", "'"), ('"', '"')):
        text = re.sub("{}.+{}".format(*delims), "", text)

    return text


def name_to_camel(words: Iterable[str]) -> str:
    """
    Converts a list of words into camelCase
    """
    words = list(words)
    cased = [words[0].lower()] + [segment.capitalize() for segment in words[1:]]
    return "".join(cased)


def name_to_snake(words: Iterable[str]) -> str:
    """
    Converts a list of words into snake_case
    """
    return "_".join([word.lower() for word in words])


def segment_string(text: str):
    """
    Divides one larger word into segments
    :param text:
    :return:
    """

    base = text.lstrip("-")

    # Replace symbols with their unicode names
    translated = re.sub(
        "[^\w\s\-_]", lambda symbol: unicodedata.name(symbol[0]).lower(), base
    )

    dash_tokens = re.split("[-_ ]", translated)
    segment_tokens = itertools.chain.from_iterable(
        [wordsegment.segment(w) for w in dash_tokens]
    )
    return [sanitize_token(tok) for tok in segment_tokens]


def generate_names(descriptions: List[str], length: int = 3) -> List[List[str]]:
    """
    Given a list of flag descriptions, iterates until it generates a set of unique names for each flag
    :param length: See :py:func:`generate_name`
    """
    #: A set of indices of flags that still need to be named
    todo = set(range(len(descriptions)))
    generators = [generate_name(desc, length=length) for desc in descriptions]
    #: A list of flag names, in the same order as the input list
    ret = [[]] * len(descriptions)
    #: A set of generators that are exhausted, meaning we can't iterate on them
    empty = set()

    # Iterate until everything is done, at most 5 more times
    for i in range(5):
        if i > 5:
            raise Exception("Variable names failed to converge")

        # Update the outputs using each generator
        for j in todo:
            try:
                # If we are able to add more characters, do so
                name = next(generators[j])
                ret[j] = name
            except StopIteration:
                # If we can't, exclude it from further calculations
                empty.add(j)

        # Clean up old generators
        new_todo = duplicate_keys(ret) - empty
        for j in todo - new_todo:
            generators[j] = None
        todo = new_todo

        # Finish once every variable name is unique
        if len(todo) == 0:
            break

    return ret


def generate_name(
    description: str, length: int = 3
) -> Generator[List[str], None, None]:
    """
    Given one or more sentences, attempt to parse out a concise (2-4 word) variable name. This is a generator, and each
    time you access it, it will return a slightly longer word, this is to help prevent collisions with other variable
    names
    :param description: One or more sentences of text to parse into a variable name
    """

    # Remove all delimited text
    sanitized = sanitize_symbols(remove_delims(replace_hyphens(description)))

    # Parse the sentence
    doc = nlp(sanitized)

    candidates = [tok for sent in doc.sents for tok in sent]
    if len(candidates) == 0:
        return []

    tokens = []
    max = length
    while True:

        # All tokens, sorted in order of importance
        candidates = sorted(
            candidates, key=lambda token: token_priority(token, tokens), reverse=True
        )

        # Each time through the loop, we increase the number of candidates we use
        if candidates:
            tokens.append(candidates.pop())

        # Iterate until we have N tokens, then yield the word. Then if the generator is called again, increase N by
        # 1 and continue

        if len(tokens) >= max or len(candidates) == 0:
            max += 1
            # Now sort the tokens back into their original positions
            yield [
                sanitize_token(str(tok)).lower()
                for tok in sorted(tokens, key=lambda tok: tok.i)
            ]
