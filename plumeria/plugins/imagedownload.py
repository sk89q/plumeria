import asyncio
import io
import logging
import re

import aiohttp
from PIL import Image
from plumeria.command import CommandError, commands
from plumeria.message import ImageAttachment, Response
from plumeria.util.http import DefaultClientSession
from plumeria.util.ratelimit import rate_limit

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024
MAX_SIZE = 1024 * 1024 * 6
MAX_LENGTH = 4000
IMAGE_LINK_PATTERN = re.compile("(https?://(?:[^ ]+)\\.(?:png|jpe?g|gif))", re.I)


@commands.register("fetchimage", category="Image")
@rate_limit()
async def fetch_image(message):
    """
    Fetch an image from a URL.
    """
    if len(message.attachments):
        return Response(message.content, message.attachments)

    m = IMAGE_LINK_PATTERN.search(message.content)
    if m:
        logger.info("Downloading image from {} for user {} in channel {}".format(m.group(1), message.author, message.channel))
        try:
            with DefaultClientSession() as session:
                async with session.get(m.group(1)) as resp:
                    if resp.status != 200:
                        raise CommandError("HTTP code is not 200; got {}".format(resp.status))

                    # check content length
                    try:
                        length = int(resp.headers['Content-Length'])
                        if length > MAX_SIZE:
                            raise CommandError("Image file has too big of a file size.")
                    except (KeyError, ValueError) as e:
                        pass

                    buffer = io.BytesIO()
                    while True:
                        chunk = await resp.content.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        buffer.write(chunk)
                        if len(buffer.getbuffer()) > MAX_SIZE:
                            raise CommandError("Image file has too big of a file size.")

            def execute():
                im = Image.open(buffer)
                width, height = im.size
                if width > MAX_LENGTH or height > MAX_LENGTH:
                    raise CommandError("Image file is too big in dimensions.")
                return im

            im = await asyncio.get_event_loop().run_in_executor(None, execute)

            return Response("", attachments=[ImageAttachment(im, m.group(1))])

        except aiohttp.errors.ClientError as e:
            logger.info("Failed to download image from {} for user {} in channel {}".format(
                m.group(1), message.author, message.channel), exc_info=True)
            raise CommandError("Failed to read image from URL.")
