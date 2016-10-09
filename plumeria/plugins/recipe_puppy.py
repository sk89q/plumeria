import re

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.message.lists import parse_list
from plumeria.util.ratelimit import rate_limit

NEW_LINES_PATTERN = re.compile("[\\r\\n]")


@commands.register("recipes", "recipe", category="Search")
@rate_limit()
async def recipes(message):
    """
    Search recipepuppy.com for recipes using a list of ingredients.

    Example::

        /recipes onions, garlic

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    ingredients = parse_list(q)
    r = await http.get("http://www.recipepuppy.com/api/", params=[
        ('i', ",".join(map(lambda s: s.replace(",", " "), ingredients))),
    ])
    data = r.json()
    if len(data['results']):
        return "\n".join(map(lambda e: NEW_LINES_PATTERN.sub("", "\u2022 **{title}** - {ingredients} <{url}>".format(
            title=e['title'].strip(),
            ingredients=e['ingredients'].strip(),
            url=e['href'].strip())), data['results'][:8]))
    else:
        raise CommandError("no results found")
