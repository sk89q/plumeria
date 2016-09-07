import re

WHITESPACE_PATTERN = re.compile("\s+")


def first_words(s, word_count=10):
    words = WHITESPACE_PATTERN.split(s, word_count + 1)
    if len(words) > word_count:
        return " ".join(words[:word_count]) + "..."
    else:
        return s
