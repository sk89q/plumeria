"""Utilities to fetch images from a message."""

import asyncio
import io
import re
from typing import Awaitable

import PIL
import aiohttp
from PIL import Image
from aiounfurl.views import fetch_all

from plumeria.command import CommandError
from plumeria.message import ImageAttachment, logger
from plumeria.message import Message
from plumeria.service import locator
from plumeria.util.http import DefaultClientSession

CHUNK_SIZE = 1024
MAX_SIZE = 1024 * 1024 * 6
MAX_LENGTH = 4000
IMAGE_LINK_PATTERN = re.compile("((https?)://[^\s/$.?#<>].[^\s<>]*)", re.I)


async def fetch_image(url: str) -> Awaitable[PIL.Image.Image]:
    """
    Fetch the image from the given URL.

    Parameters
    ----------
    url : str
        URL of the image

    Returns
    -------
    Awaitable[PIL.Image.Image]
        A PIL image

    Raises
    ------
    :class:`CommandError`
        Thrown if there is any problem fetching the image

    """
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
            if im.format.upper() != "RGBA":
                im = im.convert("RGBA")
            return im

        im = await asyncio.get_event_loop().run_in_executor(None, execute)

        return ImageAttachment(im, url)

    except aiohttp.errors.ClientError as e:
        logger.info("Failed to download image from {}".format(url), exc_info=True)
        raise CommandError("Failed to read image from URL.")


async def unfurl_image_url(url: str) -> Awaitable[str]:
    with DefaultClientSession() as session:
        results = await fetch_all(session, url)
        if 'twitter_cards' in results and 'image' in results['twitter_cards']:
            return results['twitter_cards']['image']
        if 'open_graph' in results and 'image' in results['open_graph']:
            return results['open_graph']['image']
        if 'oembed' in results and 'thumbnail_url' in results['oembed']:
            return results['oembed']['thumbnail_url']
        raise CommandError("Couldn't extract an image from the URL '{}'".format(url))


async def read_image(message: Message) -> Awaitable[PIL.Image.Image]:
    """
    Fetch the first image from the given message.

    Parameters
    ----------
    message : :class:`plumeria.transport.Message`
        The message

    Returns
    -------
    Awaitable[PIL.Image.Image]
        A PIL image

    Raises
    ------
    :class:`CommandError`
        Thrown if there is any problem getting an image

    """

    # first try looking at attachments
    for attachment in message.attachments:
        try:
            if isinstance(attachment, ImageAttachment):
                return attachment
            elif attachment.mime_type.startswith("image/"):
                im = Image.open(io.BytesIO(await attachment.read()))
                if im.format.upper() != "RGBA":
                    im = im.convert("RGBA")
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
            try:
                return await fetch_image(url)
            except OSError as e:
                return await fetch_image(await unfurl_image_url(url))

    return None
