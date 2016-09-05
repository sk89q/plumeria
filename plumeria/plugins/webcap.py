import io
import json
import logging
import re
from json import JSONDecodeError

from aiohttp import TCPConnector

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment
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


@commands.register('screenshot', 'ss', category='Utility')
@rate_limit(burst_size=2)
async def screenshot(message):
    """
    Generates a screenshot of a webpage.

    Example::

        /screenshot https://www.sk89q.com

    """
    q = message.content.strip()
    if not q:
        raise CommandError("URL required")
    m = LINK_PATTERN.search(q)
    if not m:
        raise CommandError("No URL found in input text")
    logger.debug("Fetching screenshot of {} for {}".format(m.group(1), message.author))
    with DefaultClientSession(connector=TCPConnector()) as session:
        async with session.request(method="post", url=render_url(), data=json.dumps({
            "url": m.group(1),
            "key": api_key(),
            "max_height": "4096",
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
                    raise CommandError("error occurred with status code {}: {}".format(r.status_code, r.text()))
