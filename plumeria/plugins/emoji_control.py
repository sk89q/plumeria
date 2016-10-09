import asyncio
import io
import re

from plumeria.command import commands, CommandError
from plumeria.message import Message
from plumeria.message.image import read_image
from plumeria.perms import server_admins_only
from plumeria.transport.transport import ForbiddenError

VALID_EMOJI_NAME_RE = re.compile("^[A-Za-z0-9_]{2,20}$")


@commands.register('emoji create', category='Management')
@server_admins_only
async def create_emoji(message: Message):
    """
    Creates new emoji.

    Example::

        /drawtext Hello there! | emoji create test

    Requires an input image.
    """
    attachment = await read_image(message)
    if not attachment:
        raise CommandError("No image is available to process.")

    name = message.content.strip()
    if not VALID_EMOJI_NAME_RE.match(name):
        raise CommandError("Invalid emoji name.")

    def execute():
        buffer = io.BytesIO()
        attachment.image.save(buffer, "png")
        return buffer.getvalue()

    image_data = await asyncio.get_event_loop().run_in_executor(None, execute)

    try:
        # first delete existing emoji
        for emoji in message.server.emojis:
            if not emoji.managed and emoji.name == name:
                await message.server.delete_custom_emoji(emoji)
        await message.server.create_custom_emoji(name=name, image=image_data)
        return "Emoji created."
    except ForbiddenError as e:
        raise CommandError("The bot doesn't have the permissions to do this: {}".format(str(e)))


@commands.register('emoji delete', 'emoji remove', category='Management')
@server_admins_only
async def delete_emoji(message: Message):
    """
    Delete custom emoji with a certain name.

    Example::

        /emoji delete example
    """
    name = message.content.strip()
    try:
        count = 0
        for emoji in message.server.emojis:
            if not emoji.managed and emoji.name == name:
                await message.server.delete_custom_emoji(emoji)
                count += 1
        return "{} deleted.".format(count)
    except ForbiddenError as e:
        raise CommandError("The bot doesn't have the permissions to do this: {}".format(str(e)))
