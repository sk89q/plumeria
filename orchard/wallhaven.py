"""Search for desktop wallpapers on Wallhave.cc."""

import random

from bs4 import BeautifulSoup

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


@commands.create("wallhaven", "wallbase", category="Search")
@rate_limit()
async def wallhaven(message):
    """
    Searches wallbase.cc for wallpapers and returns one wallpaper. If no query is provided,
    then a random wallpaper will be returned.

    Example::

        /wallhaven birds
    """
    query = message.content.strip()

    r = await http.get("https://alpha.wallhaven.cc/search", params=[
        ('q', query),
        ('categories', '100'),
        ('purity', '110'),
        ('sorting', 'favorites'),
        ('order', 'desc')
    ])

    results = []
    soup = BeautifulSoup(r.text(), "html.parser")
    for thumb in soup.find_all("figure", class_="thumb"):
        image = thumb.find("img")
        if image:
            image_url = image['data-src']
            link = thumb.find("a", class_="preview")['href']
            results.append((image_url, link))
    if len(results):
        choice = random.choice(results)
        return "{}\nGet it here: <{}>".format(*choice)
    else:
        raise CommandError("No wallpapers found!")


def setup():
    commands.add(wallhaven)
