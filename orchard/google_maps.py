"""Query Google Maps for maps and other geo info."""

import io
import re
import urllib.parse

import html2text

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

LOCATION_SPLIT_PATTERN = re.compile("\\bto\\b", re.IGNORECASE)

api_key = config.create("google", "key",
                        fallback="",
                        comment="An API key from https://console.developers.google.com/ with the proper APIs enabled")


@commands.create("latlng", "latlong", "lat lng", "lat long", category="Search")
@rate_limit()
async def lat_long(message):
    """
    Geocode an address and return latitude and longitude.

    Example::

        /latlng disneyworld

    Response::

        28.419185, -81.58211899999999 (Walt Disney World Monorail, Bay Lake, FL 32821, USA)

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Address required")

    r = await http.get("https://maps.googleapis.com/maps/api/geocode/json", params=[
        ('key', api_key()),
        ('address', q),
    ])
    data = r.json()
    if data['status'] == "ZERO_RESULTS":
        raise CommandError("Address could not be matched to any location")
    elif data['status'] == "OK":
        entry = data['results'][0]
        return "{}, {} ({})".format(entry['geometry']['location']['lat'],
                                    entry['geometry']['location']['lng'],
                                    entry['formatted_address'])
    else:
        raise CommandError("Google Maps returned an error: {}".format(
            data['error_message'] if 'error_message' in data else data['status']))


@commands.create("directions", category="Search")
@rate_limit()
async def directions(message):
    """
    Get driving directions between two places using Google Maps.
    Separate origin and destination with the word "to".

    Example::

        /directions oakland, ca to los angeles, ca

    The output can take up a lot of lines. If there are too many lines to fit into
    a Discord message, the entire output will be attached as a text file.

    Response::

        372 mi (5 hours 24 mins)
        1. Head southwest on Broadway toward 14th St (4 mins)
        2. Turn left onto 5th St (1 min)
        3. Take the ramp on the left onto I-880 S (10 mins)
        4. Take exit 31 for I-238 toward Stockton/Fresno/I-580 (1 min)
        5. Keep left to continue toward I-238 S (1 min)
        6. Keep left at the fork, follow signs for I-238/I-880/Castro Valley/Stockton Fresno (1 min)
        [...]

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Origin and destination required!")
    parts = LOCATION_SPLIT_PATTERN.split(q)
    if len(parts) != 2:
        raise CommandError("Origin and destination required! Separate with one mention of the word 'to'.")
    origin, destination = map(lambda s: s.strip(), parts)
    if not len(origin):
        raise CommandError("Empty origin provided")
    if not len(destination):
        raise CommandError("Empty destination provided")

    r = await http.get("https://maps.googleapis.com/maps/api/directions/json", params=[
        ('key', api_key()),
        ('origin', origin),
        ('destination', destination),
    ])
    data = r.json()
    if data['status'] == "NOT_FOUND":
        raise CommandError("Either or both the origin and destination were not found")
    elif data['status'] == "ZERO_RESULTS":
        raise CommandError("No routes found")
    elif data['status'] == "OK":
        buffer = io.StringIO()
        for leg in data['routes'][0]['legs']:
            buffer.write(":map: {} ({}) <https://maps.google.com/?q={}>\n".format(
                leg['distance']['text'], leg['duration']['text'], urllib.parse.quote(q)))
            for i, step in enumerate(leg['steps']):
                buffer.write("{}. {} ({})\n".format(i + 1, html2text.html2text(step['html_instructions']).replace("\n",
                                                                                                                  " ").strip(),
                                                    step['duration']['text']))
        return buffer.getvalue().strip()
    else:
        raise CommandError("Google Maps returned an error: {}".format(
            data['error_message'] if 'error_message' in data else data['status']))


@commands.create("map", category="Search", params=[Text('location')])
@rate_limit()
async def map(message, location):
    """
    Get a map from Google Maps of a location.

    Example::

        /map san francisco

    """
    return 'https://maps.googleapis.com/maps/api/staticmap?' + urllib.parse.urlencode({
        'center': location,
        'size': '640x350'
    })


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from Google. Registration is free. Get keys from "
                               "https://console.developers.google.com.")

    commands.add(lat_long)
    commands.add(directions)
    commands.add(map)
