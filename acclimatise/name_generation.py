import re
from typing import Iterable, List

import spacy


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


def remove_delims(text):
    for delims in (("\[", "\]"), ("\(", "\)"), ("{", "}"), ("'", "'"), ('"', '"')):
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


def generate_name(description: str) -> Iterable[str]:
    """
    Given one or more sentences, attempt to parse out a concise (2-4 word) variable name
    """
    try:
        nlp = spacy.load("en")
    except IOError:
        raise Exception(
            "Spacy model doesn't exist! Install it with `python -m spacy download en`"
        )

    # Remove all delimited text
    no_brackets = remove_delims(description)

    # Parse the sentence
    doc = nlp(no_brackets)
    sentence = list(doc.sents)[0]
    root = sentence.root

    # Add the second most important word after the root
    candidates = sorted(
        [
            (distance_to_root(tok, root), tok)
            for tok in sentence
            if not should_ignore(tok) and root != tok
        ]
    )
    tokens = [root] if len(candidates) == 0 else [root, candidates[0][1]]

    # Add any adjectives/adverbs that describe either word
    for tok in tokens:
        for child in tok.children:
            if child.pos_ in {"ADV", "ADJ"}:
                tokens.append(child)

    # If we still don't have 3 tokens, add the 3rd most important
    if len(tokens) < 3 and len(candidates) >= 2:
        tokens.append(candidates[1][1])

    # Now sort the tokens back into their original positions
    return [str(tok).lower() for tok in sorted(tokens, key=lambda tok: tok.i)]
