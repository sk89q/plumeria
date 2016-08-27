import asyncio
import io
import re

import aiohttp
from PIL import Image

from plumeria.command import CommandError
from plumeria.message import logger, ImageAttachment
from plumeria.service import locator
from plumeria.util.http import DefaultClientSession

CHUNK_SIZE = 1024
MAX_SIZE = 1024 * 1024 * 6
MAX_LENGTH = 4000
IMAGE_LINK_PATTERN = re.compile("((https?)://[^\s/$.?#<>].[^\s<>]*)", re.I)
MARKDOWN_ESCAPE_PATTERN = re.compile("([\\*_`\\{\\}\\[\\]\\-~])")


def escape_markdown(s):
    return MARKDOWN_ESCAPE_PATTERN.sub("\\\\\\1", s)


async def fetch_image(url):
    try:
        with DefaultClientSession() as session:
            async with session.get(url) as resp:
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
            if im.format != "RGB":
                im = im.convert("RGB")
            return im

        im = await asyncio.get_event_loop().run_in_executor(None, execute)

        return ImageAttachment(im, url)

    except aiohttp.errors.ClientError as e:
        logger.info("Failed to download image from {}".format(url), exc_info=True)
        raise CommandError("Failed to read image from URL.")


async def read_image(message):
    # first try looking at attachments
    for attachment in message.attachments:
        try:
            if isinstance(attachment, ImageAttachment):
                return attachment
            elif attachment.mime_type.startswith("image/"):
                im = Image.open(io.BytesIO(await attachment.read()))
                if im.format != "RGB":
                    im = im.convert("RGB")
                return ImageAttachment(im, attachment.filename)
        except IOError as e:
            raise CommandError("Failed to read image from message.")

    # then check if a service has a value
    value = await locator.first_value("message.read_image", message)

    # check for URL
    if not value:
        m = IMAGE_LINK_PATTERN.search(message.content)
        if m:
            url = m.group(1).strip()
            logger.info(
                "Downloading image from {} for user {} in channel {}".format(
                    url, message.author, message.channel))
            # hack to modify message because the URL appears in arguments
            message.content = message.content.replace(m.group(1), "", 1)
            return await fetch_image(url)

    return None


def parse_list(s, allow_spaces=True):
    s = s.strip()
    if '\n' in s:
        delimiter = '\n'
    elif ';' in s:
        delimiter = ';'
    elif ',' in s:
        delimiter = ','
    elif allow_spaces:
        delimiter = " "
    else:
        return [s]

    return list(filter(lambda s: len(s), map(lambda s: s.strip(), s.split(delimiter))))


def parse_numer_list(s):
    numbers = parse_list(s)
    try:
        return list(map(lambda x: float(x), numbers))
    except ValueError as e:
        raise CommandError("All the entries must be numbers")
