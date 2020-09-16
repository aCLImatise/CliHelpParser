import itertools
import unicodedata
from collections import Counter, defaultdict
from difflib import ndiff, unified_diff
from itertools import groupby
from typing import Generator, Iterable, List, Optional, Set, Tuple

import regex as re
from num2words import num2words
from spacy.tokens import Token
from word2number import w2n

from aclimatise.nlp import nlp, wordsegment


class NameGenerationError(Exception):
    def __init__(self, message: str):
        self.message = message


def useless_name(name: List[str]):
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


def ensure_first_alpha(text):
    return re.sub(r"\b[^[:alpha:]\s]", "", text)


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


def token_priority(token: Token, current: List[Token], key: Set[Token] = set()) -> int:
    """
    Returns a priority (where lowest means highest priority) of tokens
    :param token: The token to prioritise
    :param current: The current list of tokens in the name
    """
    if token in key:
        # Tokens that are "keywords" are the highest priority
        return token.idx - 1000

    if token.pos_ not in {"NOUN", "NUM", "PRON", "PROPN", "VERB", "ADJ", "ADV"}:
        # Tokens that have meaningful POS are prioritised
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


def human_readable_translate(symbol: str):
    # First, if the symbol is in this small curated list, use that
    lookup = {".": "dot", ",": "comma", "/": "slash", "\\": "backslash", "@": "at"}
    if symbol in lookup:
        return lookup[symbol]

    # Second, if the symbol is a number, convert it to natural English
    try:
        return num2words(symbol, ordinal=False, lang="en", to="cardinal")
    except Exception:
        # If it's not a number, ignore the error
        pass

    # Finally, if neither of those worked, ask unicode what it should be called
    # This isn't ideal because unicodedata calls "/" a "SOLIDUS" and "@" it calls "commercial at", which is rather
    # awkward
    return unicodedata.name(symbol[0]).lower()


def segment_string(text: str):
    """
    Divides one larger word into segments
    :param text:
    :return:
    """

    base = text.lstrip("-")

    # Replace symbols with their unicode names
    translated = re.sub(
        "[^[:alpha:]\s\-_]", lambda match: human_readable_translate(match.group()), base
    )

    dash_tokens = re.split("[-_ ]", translated)
    segment_tokens = itertools.chain.from_iterable(
        [wordsegment.segment(w) for w in dash_tokens]
    )
    return [sanitize_token(tok) for tok in segment_tokens]


def choose_unique_name(
    options: Tuple[List[str], ...], number: int, reserved: Set[Tuple[str, ...]] = []
) -> List[str]:
    """
    Given a list of possible names for each flag, choose the first one that is not too short
    """
    # First try all of them, being picky
    for option in options:
        if tuple(option) in reserved:
            # If name generation produces a reserved keyword, skip it
            continue
        if not useless_name(option):
            return option

    # Second, try all of them choosing anything that isn't empty
    for option in options:
        if tuple(option) in reserved:
            # If name generation produces a reserved keyword and we've already tried everything else, add "var" to it as a prefix
            return ["var", *option]
        if len(option) == 1 and option[0] in reserved:
            continue
        if len(option) > 0:
            return option

    # If nothing else works, just use something like 'var_3' as the variable name
    return ["var", str(number)]
    # raise NameGenerationError(
    #     "No unique names available. Selecting from {}".format(
    #         ";".join([" ".join(option) for option in options])
    #     )
    # )


def generate_names_segment(
    descriptions: List[str], initial_length: int = 3, max_length: int = 5
) -> List[List[str]]:
    """
    Given a list of short strings, one for each variable, we segment each string. Any duplicate names are set to an
    empty list as they are unusable
    """
    segmented = [segment_string(desc) for desc in descriptions]
    for dup in duplicate_keys(segmented):
        segmented[dup] = []
    return segmented

    # todo = set(range(len(descriptions)))
    # segmented = [segment_string(desc) for desc in descriptions]
    # ret = [[]] * len(descriptions)
    # empty = set()
    #
    # # Increase the maximum length each iteration
    # for length in range(initial_length, max_length + 1):
    #
    #     # If we run out of iterations and still haven't converged, these variables names become empty
    #     if length >= max_length:
    #         for j in todo:
    #             ret[j] = []
    #         return ret
    #
    #     # Update the outputs using each generator
    #     for j in todo:
    #         # If this token is still not unique, but it has no more characters left, it's a lost cause
    #         if length > len(segmented[j]):
    #             empty.add(j)
    #             ret[j] = []
    #         ret[j] = segmented[j][:length]
    #
    #     # Clean up old generators
    #     todo = duplicate_keys(ret) - empty
    #
    #     return ret


def intersection_indices(
    l: List[List[str]], reserved: Set[Tuple[str, ...]]
) -> Set[int]:
    """
    Returns a set of indices from ``l`` that occur in the set of reserved keywords
    """
    ret = set()
    for i, words in enumerate(l):
        if tuple(words) in reserved:
            ret.add(i)
    return ret


def find_key_diff_words(
    descriptions: List[List[Token]], after_index: int = 5
) -> List[Set[Token]]:
    """
    Returns a list of words for each description that uniquely identifies each
    :param after_index: The index in the string after which to consider key words. Because we always include the first
    few words in generated names, finding diffs at these positions isn't helpful
    """
    desc_strings = [[str(token) for token in desc] for desc in descriptions]
    ret = [set() for d in descriptions]
    for i, description_a in enumerate(descriptions):
        for j, description_b in enumerate(descriptions):
            if i == j:
                # Don't compare a word to itself
                continue

            # Keep iterating until we find the first diff, then add the diff words to a list of key words
            for k, diff in enumerate(ndiff(desc_strings[i], desc_strings[j])):
                if diff[0] in ["+", "-"]:
                    if k > after_index:
                        # If this token differs, add the difference
                        if len(description_a) > k:
                            ret[i].add(description_a[k])
                        if len(description_b) > k:
                            ret[j].add(description_b[k])

                    # Always break once we find a diff
                    break

    return ret


def preprocess(text: str) -> List[Token]:
    """
    Pre-process some text, remove and unnecessary tokens, and return the Spacy data structure
    """
    # Remove all delimited text
    sanitized = ensure_first_alpha(
        sanitize_symbols(remove_delims(replace_hyphens(text)))
    )

    # Parse the sentence
    doc = nlp(sanitized)

    candidates = [tok for sent in doc.sents for tok in sent]
    if len(candidates) == 0:
        return []
    else:
        return candidates


def generate_names_nlp(
    descriptions: List[str],
    initial_length: int = 3,
    max_length: int = 5,
    reserved: Set[Tuple[str, ...]] = set(),
) -> List[List[str]]:
    """
    Given a list of flag descriptions, iterates until it generates a set of unique names for each flag
    :param initial_length: The minimum/starting length for each variable name
    :param max_length: The maximum length variables can have before it will fail
    :param reserved: Keywords that are not permitted to be used as the entire name
    """
    #: A set of indices of flags that still need to be named
    todo = set(range(len(descriptions)))

    # Preprocessing
    processed = list(map(preprocess, descriptions))
    diffs = find_key_diff_words(processed)
    generators = [
        generate_name(proc, initial_length=initial_length, key_words=keywords)
        for proc, keywords in zip(processed, diffs)
    ]
    #: A list of flag names, in the same order as the input list
    ret = [[]] * len(descriptions)
    #: A set of generators that are exhausted, meaning we can't iterate on them
    empty = set()

    # Iterate until everything is done, at most 5 more times
    for i in range(max_length + 1):
        if i >= max_length:
            # If we run out of iterations and still haven't converged, these variables names become empty
            for j in todo:
                ret[j] = []
            return ret
            # raise Exception("Variable names failed to converge")

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
        new_todo = duplicate_keys(ret) | intersection_indices(ret, reserved) - empty
        for j in todo - new_todo:
            generators[j] = None
        todo = new_todo

        # Finish once every variable name is unique
        if len(todo) == 0:
            break

    return ret


def generate_name(
    tokens: List[Token], initial_length: int = 3, key_words: Set[Token] = set()
) -> Generator[List[str], None, None]:
    """
    Given one or more sentences, attempt to parse out a concise (2-4 word) variable name. This is a generator, and each
    time you access it, it will return a slightly longer word, this is to help prevent collisions with other variable
    names
    :param tokens: One or more sentences of text that have been pre-processed
    :param initial_length: The number of words in the first output this produces
    """
    candidates = tokens
    ret = [*key_words]
    max = initial_length
    while True:

        # All tokens, sorted in order of importance
        candidates = sorted(
            candidates, key=lambda token: token_priority(token, ret), reverse=True
        )

        # Each time through the loop, we increase the number of candidates we use
        if candidates:
            ret.append(candidates.pop())

        # Iterate until we have N tokens, then yield the word. Then if the generator is called again, increase N by
        # 1 and continue

        if len(ret) >= max or len(candidates) == 0:
            max += 1
            # Now sort the tokens back into their original positions
            yield [
                sanitize_token(str(tok)).lower()
                for tok in sorted(ret, key=lambda tok: tok.i)
            ]
