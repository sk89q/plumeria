import re

import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit

MINECRAFT_STATUS_URL = "http://xpaw.ru/mcstatus/status.json"
HEADERS = {"Cookie": "__cfduid=d100ef4ed084175f2382f35613cb9c9dc1458598283"}
VALID_NAME = re.compile("^[A-Za-z0-9_]{1,30}$")
VALID_UUID = re.compile(
    "(?:[A-Fa-f0-9]{32}|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12})")


def validate_name(name):
    name = name.strip()
    if not VALID_NAME.match(name):
        raise CommandError("Invalid Minecraft name given")
    return name


def validate_uuid(uuid):
    m = VALID_UUID.search(uuid)
    if m:
        return m.group(0).replace("-", "")
    raise CommandError("Invalid UUID given")


@commands.register("mcstatus", category="Minecraft")
@rate_limit()
async def mc_status(message):
    """
    Get the status of Minecraft's services.

    Example::

        /mcstatus

    Response::

        Realms: OK, Login: OK, Skins: OK, Website: OK, Session: OK

    """
    r = await http.get(MINECRAFT_STATUS_URL, headers=HEADERS)
    data = r.json()['report']
    status = []
    for name, v in data.items():
        text = v['title']
        if text == "Online":
            text = ":ok:"
        else:
            text = ":warning: " + text
        status.append("{}: {}".format(name.title(), text))
    return Response(", ".join(status))


@commands.register("mcuuid", category="Minecraft")
@rate_limit()
async def mc_uuid(message):
    """
    Get the UUID of a Minecraft user.
    """
    name = validate_name(message.content)
    try:
        r = await http.get("https://us.mc-api.net/v3/uuid/" + name)
        return Response(r.json()['uuid'])
    except http.BadStatusCodeError as e:
        if e.http_code == 404:
            raise CommandError("No user found by that name")
        raise CommandError("API returned an error code")


@commands.register("mcnames", category="Minecraft")
@rate_limit()
async def mc_name_history(message):
    """
    Get the name history of a UUID.
    """
    uuid = validate_uuid(message.content)
    try:
        r = await http.get("https://us.mc-api.net/v3/history/" + uuid)
        return Response(", ".join([i['name'] for i in r.json()['history']]))
    except http.BadStatusCodeError as e:
        if e.http_code == 404:
            raise CommandError("No user found by that UUID")
        raise CommandError("API returned an error code")
