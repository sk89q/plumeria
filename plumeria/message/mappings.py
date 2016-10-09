import re
from typing import Tuple, Sequence

from plumeria.util.collections import CaseInsensitiveDict
from plumeria.message.lists import build_list, parse_list

MAPPING_RE = re.compile("^\\**([^:\\*]+):?\\**:?(.*)$")


def parse_mapping(s):
    mapping = []
    lines = parse_list(s, allow_spaces=False)
    for line in lines:
        m = MAPPING_RE.search(line)
        if m:
            mapping.append((m.group(1).strip(), m.group(2)))
    return mapping


def build_mapping(items: Sequence[Tuple[str, str]]):
    return build_list(["**{}:** {}".format(*e) for e in items])
