"""Utility methods to accept lists provided from user input or to generate lists to return in responses."""

import re
from typing import List, Sequence

from plumeria.command import CommandError

LIST_CLEAN_RE = re.compile("^\N{BULLET} +")


def parse_list(s: str, allow_spaces: bool = True, maxsplit: int = -1) -> List[str]:
    """
    Very liberally try to parse a list from the supplied input. List items could
    be separated by commas, semi-colons, new lines, and if permitted, spaces.

    The returned list may contain only one item, and that one item may be an empty string.

    Parameters
    ----------
    s : str
        User input to parse
    allow_spaces : bool
        Whether to allow entries to be separated by spaces
    maxsplit : int
        Maximum number of splits, or -1 for no maximum

    Returns
    -------
    List[str]

    """

    s = s.strip()
    if '\n' in s:
        delimiter = '\n'
    elif ';' in s:
        delimiter = ';'
    elif ',' in s:
        delimiter = ','
    elif allow_spaces:
        delimiter = " "
    else:
        return [s]

    items = list(
        filter(lambda s: len(s), map(lambda s: LIST_CLEAN_RE.sub('', s.strip()), s.split(delimiter, maxsplit))))
    if len(items):
        return items
    else:
        return [""]


def parse_numeric_list(s: str) -> List[float]:
    """
    Parse a list of numbers.

    Parameters
    ----------
    s : str
        User input

    Returns
    -------
    List[float]
        A list of numbers

    """
    numbers = parse_list(s)
    try:
        return list(map(lambda x: float(x), numbers))
    except ValueError as e:
        raise CommandError("All the entries must be numbers")


def build_list(items: Sequence[str]) -> str:
    """
    Return the text for a list of items to be sent to the user.

    Parameters
    ----------
    items : Sequence[str]
        List of items

    Returns
    -------
    str
        The list text

    """
    return "\n".join(["\N{BULLET} " + str(i) for i in items])
