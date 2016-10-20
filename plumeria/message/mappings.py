"""Utility methods to accept mappings provided from user input or to generate mappings to return in responses."""

import re
from typing import Tuple, Sequence

from plumeria.message.lists import build_list, parse_list

MAPPING_RE = re.compile("^\\**([^:\\*]+):?\\**:?(.*)$")


def parse_mapping(s: str) -> Sequence[Tuple[str, str]]:
    """
    Parse mappings from user input.

    Parameters
    ----------
    s : str
        User input string

    Returns
    -------
    Sequence[Tuple[str, str]]
        List of mappings

    """
    mapping = []
    lines = parse_list(s, allow_spaces=False)
    for line in lines:
        m = MAPPING_RE.search(line)
        if m:
            mapping.append((m.group(1).strip(), m.group(2)))
    return mapping


def build_mapping(items: Sequence[Tuple[str, str]]):
    """
    Generate a string to represent a mapping.

    Parameters
    ----------
    items : Sequence[Tuple[str, str]]
        Mapping

    Returns
    -------
    str
        String version of mappings

    """
    return build_list(["**{}:** {}".format(*e) for e in items])
