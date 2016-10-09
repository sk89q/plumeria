from plumeria.command import CommandError


def parse_list(s, allow_spaces=True):
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

    return list(filter(lambda s: len(s), map(lambda s: s.strip(), s.split(delimiter))))


def parse_numeric_list(s):
    numbers = parse_list(s)
    try:
        return list(map(lambda x: float(x), numbers))
    except ValueError as e:
        raise CommandError("All the entries must be numbers")


def build_list(items):
    return "\n".join(["\N{BULLET} " + str(i) for i in items])
