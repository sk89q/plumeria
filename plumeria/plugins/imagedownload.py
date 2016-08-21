import asyncio
import io
import logging
import re

import aiohttp
from PIL import Image
from plumeria.command import CommandError, commands
from plumeria.message import ImageAttachment, Response
from plumeria.util.message import read_image
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
    return Response("", attachments=[await read_image(message)])
