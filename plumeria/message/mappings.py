from typing import Tuple, Sequence

from plumeria.message.lists import build_list


def build_mapping(items: Sequence[Tuple[str, str]]):
    return build_list(["**{}:** {}".format(*e) for e in items])
