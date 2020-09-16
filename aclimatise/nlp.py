import spacy
import wordsegment

# We load the spacy and the wordsegment models here as a kind of singleton pattern, to avoid multiple functions loading
# redundant copies

if len(wordsegment.WORDS) == 0:
    wordsegment.load()


try:
    nlp = spacy.load("en")
except IOError:
    raise Exception(
        "Spacy model doesn't exist! Install it with `python -m spacy download en`"
    )
