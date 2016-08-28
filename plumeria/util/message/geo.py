import pycountry

from plumeria.command import CommandError


def match_country(q):
    candidates = []
    for country in pycountry.countries:
        if q.lower() in (country.name.lower(), country.alpha2.lower(), country.alpha3.lower()):
            candidates.append((country, 1))
        elif q.lower() in country.name.lower():
            candidates.append((country, 0.5))
    candidates.sort(key=lambda e: -e[1])
    if not len(candidates):
        raise CommandError("no match of any country")
    return candidates[0][0]
