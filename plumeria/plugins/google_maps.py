import io
import re
import urllib.parse

import html2text

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

LOCATION_SPLIT_PATTERN = re.compile("\\bto\\b", re.IGNORECASE)

api_key = config.create("google", "key",
                        fallback="",
                        comment="An API key from https://console.developers.google.com/ with the proper APIs enabled")


@commands.register("latlng", "latlong", "lat lng", "lat long", category="Search")
@rate_limit()
async def lat_long(message):
    """
    Geocode an address and return latitude and longitude.

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


@commands.register("directions", category="Search")
@rate_limit()
async def directions(message):
    """
    Get driving directions between two places using Google Maps.
    Separate origin and destination with the word "to".

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
            buffer.write(":map: {} ({}) <http://maps.google.com/?q={}>\n".format(
                leg['distance']['text'], leg['duration']['text'], urllib.parse.urlencode(q)))
            for i, step in enumerate(leg['steps']):
                buffer.write("{}. {} ({})\n".format(i + 1, html2text.html2text(step['html_instructions']).replace("\n",
                                                                                                                  " ").strip(),
                                                    step['duration']['text']))
        return buffer.getvalue().strip()
    else:
        raise CommandError("Google Maps returned an error: {}".format(
            data['error_message'] if 'error_message' in data else data['status']))
