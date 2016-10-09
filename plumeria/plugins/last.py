import collections
import re

from plumeria.command import commands, CommandError, channel_only
from plumeria.message import Response
from plumeria.event import bus
from plumeria.util.ratelimit import rate_limit

LINK_PATTERN = re.compile("https?://([^ ><]+)", re.I)
IMAGE_PATTERN = re.compile("https?://([^ ><]+)\\.(?:png|jpe?g|gif)", re.I)


class LastMessage:
    def __init__(self):
        self._loaded = False
        self.last_text = None
        self.last_url = None
        self.last_image = None

    @property
    def loaded(self):
        return self._loaded or (self.last_text and self.last_url and self.last_image)

    def read(self, message):
        m = LINK_PATTERN.search(message.content)
        if m:
            self.last_url = Response(m.group(0))
        m = IMAGE_PATTERN.search(message.content)
        if m:
            self.last_image = Response(m.group(0))
        else:
            for attachment in message.attachments:
                if attachment.mime_type.startswith("image/"):
                    self.last_image = Response("", attachments=[attachment.copy()])
        if len(message.content.strip()) and not commands.matches_command(message.content):
            self.last_text = Response(message.content)

    async def load_if_unloaded(self, channel):
        if not self.loaded:
            messages = []
            async for message in channel.get_history(limit=100):
                messages.insert(0, message)
            for message in messages:
                self.read(message)
            self._loaded = True


history = collections.defaultdict(lambda: collections.defaultdict(lambda: LastMessage()))


@bus.event("channel.delete")
async def on_channel_delete(channel):
    if channel.server.id in history:
        if channel.id in history[channel.server.id]:
            del history[channel.server.id][channel.id]


@bus.event("server.remove")
async def on_server_remove(server):
    if server.id in history:
        del history[server.id]


@bus.event("message")
@bus.event("self_message")
async def on_message(message):
    channel = message.channel
    if not channel.is_private:
        history[channel.server.id][channel.id].read(message)


@commands.register('last text', 'lasttext', 'last', category='Utility')
@channel_only
async def last_text(message):
    """
    Gets the last non-command message said in a channel.

    Example::

        /last
    """
    channel = message.channel
    last_data = history[channel.server.id][channel.id]
    await last_data.load_if_unloaded(channel)
    value = last_data.last_text
    if value:
        return value
    else:
        raise CommandError("No last value found.")


@commands.register('last image', 'lastimage', category='Utility')
@channel_only
async def last_image(message):
    """
    Gets the last image posted in a channel, which could either be a URL or an attachment.

    Example::

        /last image
    """
    channel = message.channel
    last_data = history[channel.server.id][channel.id]
    await last_data.load_if_unloaded(channel)
    value = last_data.last_image
    if value:
        return value
    else:
        raise CommandError("No last value found.")


@commands.register('last url', 'lasturl', 'last link', 'lastlink', category='Utility')
@channel_only
async def last_image(message):
    """
    Gets the last link posted in a channel.

    Example::

        /last url
    """
    channel = message.channel
    last_data = history[channel.server.id][channel.id]
    await last_data.load_if_unloaded(channel)
    value = last_data.last_url
    if value:
        return value
    else:
        raise CommandError("No last value found.")
