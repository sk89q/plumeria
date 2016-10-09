import asyncio

from functools import wraps
from ..command import CommandError
from ..message import Response
from plumeria.message.image import read_image
from ..util.ratelimit import rate_limit


def image_filter(f):
    @wraps(f)
    @rate_limit(burst_size=2)
    async def wrapper(message):
        attachment = await read_image(message)
        if not attachment:
            raise CommandError("No image is available to process.")

        def execute():
            attachment.image = f(message, attachment.image)

        await asyncio.get_event_loop().run_in_executor(None, execute)
        return Response("", [attachment])

    return wrapper


def string_filter(f):
    @wraps(f)
    async def wrapper(message):
        def execute():
            return f(message.content)

        return Response(await asyncio.get_event_loop().run_in_executor(None, execute))

    return wrapper


def add_doc(value):
    def wrapper(func):
        func.__doc__ = value
        return func

    return wrapper
