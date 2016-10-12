import re

WHITESPACE_PATTERN = re.compile("\s+")


def first_words(s, word_count=10):
    words = WHITESPACE_PATTERN.split(s, word_count + 1)
    if len(words) > word_count:
        return " ".join(words[:word_count]) + "..."
    else:
        return s


def best_match_distance(target, query):
    target_lower = target.lower()
    query_lower = query.lower()
    if target == query:
        return -3
    elif target_lower == query_lower:
        return -2
    else:
        return len(target_lower.replace(query_lower, "")) / len(target) - 1


def get_best_matching(items, query, key):
    measured = [(best_match_distance(key(item), query), item) for item in items]
    filtered = [entry for entry in measured if entry[0] != 0]
    best = sorted(filtered, key=lambda entry: entry[0])
    return [entry[1] for entry in best]
