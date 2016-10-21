"""Commands to query Minecraft service status and user information."""

import re

import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit

MINECRAFT_STATUS_URL = "http://xpaw.ru/mcstatus/status.json"
HEADERS = {"Cookie": "__cfduid=d100ef4ed084175f2382f35613cb9c9dc1458598283"}
VALID_NAME = re.compile("^[A-Za-z0-9_]{1,30}$")
VALID_UUID = re.compile(
    "(?:[A-Fa-f0-9]{32}|[A-Fa-f0-9]{8}-?[A-Fa-f0-9]{4}-?[A-Fa-f0-9]{4}-?[A-Fa-f0-9]{4}-?[A-Fa-f0-9]{12})")


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


async def name_to_uuid(name):
    m = VALID_UUID.search(name)
    if m:
        return m.group(0)
    name = validate_name(name)
    r = await http.get("https://mcapi.ca/uuid/player/" + name)
    results = r.json()
    if len(results):
        return results[0]['uuid_formatted']
    else:
        raise CommandError("user not found")


@commands.create("minecraft status", "mcstatus", category="Games")
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


@commands.create("minecraft uuid", "mcuuid", category="Games")
@rate_limit()
async def mc_uuid(message):
    """
    Get the UUID of a Minecraft user.
    """
    name = validate_name(message.content)
    try:
        return await name_to_uuid(name)
    except http.BadStatusCodeError as e:
        if e.http_code == 404:
            raise CommandError("No user found by that name")
        raise CommandError("API returned an error code")


@commands.create("minecraft body", "mcbody", category="Games")
@rate_limit()
async def mc_body(message):
    """
    Get the rendered 3D body for a Minecraft user with his or her skin.

    Example::

        /mcbody sk89q

    """
    return "https://crafatar.com/renders/body/{}".format(await name_to_uuid(message.content))


@commands.create("minecraft head", "mchead", category="Games")
@rate_limit()
async def mc_head(message):
    """
    Get the rendered 3D head for a Minecraft user with his or her skin.

    Example::

        /mchead sk89q

    """
    return "https://crafatar.com/renders/head/{}".format(await name_to_uuid(message.content))


@commands.create("minecraft face", "mcface", category="Games")
@rate_limit()
async def mc_face(message):
    """
    Get the face for a Minecraft user with his or her skin.

    Example::

        /mcface sk89q

    """
    return "https://crafatar.com/avatars/{}".format(await name_to_uuid(message.content))


@commands.create("minecraft skin", "mcskin", category="Games")
@rate_limit()
async def mc_skin(message):
    """
    Get the skin for a Minecraft user.

    Example::

        /mcskin sk89q

    """
    return "https://crafatar.com/skins/{}".format(await name_to_uuid(message.content))


@commands.create("minecraft cape", "mccape", category="Games")
@rate_limit()
async def mc_cape(message):
    """
    Get the cape for a Minecraft user.

    Example::

        /mccape sk89q

    """
    return "https://crafatar.com/capes/{}".format(await name_to_uuid(message.content))


def setup():
    commands.add(mc_status)
    commands.add(mc_uuid)
    commands.add(mc_body)
    commands.add(mc_head)
    commands.add(mc_face)
    commands.add(mc_skin)
    commands.add(mc_cape)
