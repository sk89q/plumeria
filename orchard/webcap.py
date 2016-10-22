"""Render HTML and webpages to images."""

import io
import json
import logging
import re
from json import JSONDecodeError

from aiohttp import TCPConnector

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment
from plumeria.plugin import PluginSetupError
from plumeria.util.http import DefaultClientSession
from plumeria.util.ratelimit import rate_limit

LINK_PATTERN = re.compile("((https?)://[^\s/$.?#<>].[^\s<>]*)", re.I)

render_url = config.create("webcap", "render_url",
                           fallback="http://localhost:8110/webcap-server/render/",
                           comment="The URL to the webcap server render API")

api_key = config.create("webcap", "key",
                        fallback="",
                        comment="The API key for the webcap server")

logger = logging.getLogger(__name__)


@rate_limit(burst_size=2)
async def render(url, width=1024, max_height=4096, trim_image=False):
    with DefaultClientSession(connector=TCPConnector()) as session:
        async with session.request(method="post", url=render_url(), data=json.dumps({
            "url": url,
            "key": api_key(),
            "width": str(width),
            "max_height": str(max_height),
            "trim": "true" if trim_image else "false",
        })) as r:
            if r.status == 200:
                buffer = io.BytesIO()
                buffer.write(await r.read())
                return Response("", attachments=[MemoryAttachment(buffer, "screenshot.jpg", "image/jpeg")])
            else:
                try:
                    data = await r.json()
                    raise CommandError("error occurred: {}".format(data['error']))
                except JSONDecodeError:
                    raise CommandError("error occurred with status code {}".format(r.status))


@commands.create('screenshot', 'ss', 'screenshot desktop', 'ss desktop', category='Utility')
async def screenshot(message):
    """
    Generates a screenshot of a webpage.

    Example::

        /ss https://www.sk89q.com

    """
    q = message.content.strip()
    if not q:
        raise CommandError("URL required")
    m = LINK_PATTERN.search(q)
    if not m:
        raise CommandError("No URL found in input text")
    url = m.group(1)
    logger.debug("Fetching screenshot of {} for {}".format(url, message.author))
    return await render(url)


@commands.create('screenshot mobile', 'ss mobile', category='Utility')
async def screenshot_mobile(message):
    """
    Generates a (mobile) screenshot of a webpage.

    Example::

        /ss mobile https://www.sk89q.com

    """
    q = message.content.strip()
    if not q:
        raise CommandError("URL required")
    m = LINK_PATTERN.search(q)
    if not m:
        raise CommandError("No URL found in input text")
    url = m.group(1)
    logger.debug("Fetching mobile screenshot of {} for {}".format(url, message.author))
    return await render(url, width=410, max_height=1024)


@commands.create('render crop', 'render', category='Utility')
async def render_html(message):
    """
    Generates a screenshot of some HTML. Crops out whitespace.

    Example::

        /render Hello <strong>world</b>!

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Some HTML required")
    return await render("data:text/html," + q, trim_image=True)


@commands.create('render full', 'renderf', category='Utility')
async def render_html_full(message):
    """
    Generates a screenshot of some HTML without cropping.

    Example::

        /renderf Hello <strong>world</b>!

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Some HTML required")
    return await render("data:text/html," + q, trim_image=False)


def setup():
    config.add(render_url)
    config.add(api_key)

    if not render_url():
        raise PluginSetupError("A render URL must be configured in order to use this "
                               "plugin. The actual rendering occurs on the separate webcap_server "
                               "plugin, which should be in hosted in an isolated environment.")

    if not api_key():
        raise PluginSetupError("This plugin requires an API key for the webcap render server. Simply run the "
                               "webcap server (ideally on a separate, isolated system) and copy the API key "
                               "that was generated.")

    commands.add(screenshot)
    commands.add(screenshot_mobile)
    commands.add(render_html)
    commands.add(render_html_full)
