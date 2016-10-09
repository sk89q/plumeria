from datetime import datetime
from distutils.util import strtobool


def boolstr(d):
    if isinstance(d, bool):
        return d
    else:
        return strtobool(d)


def dateformatstr(s):
    datetime.now().strftime(s)
    return s


def list_of(type=str):
    def reader(s):
        items = s.split(",")
        items = map(lambda s: s.strip(), items)
        items = filter(lambda s: len(s), items)
        return [type(s) for s in items]

    return reader


def set_of(type=str):
    def reader(s):
        items = s.split(",")
        items = map(lambda s: s.strip(), items)
        items = filter(lambda s: len(s), items)
        return {type(s) for s in items}

    return reader
