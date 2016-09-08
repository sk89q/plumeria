import asyncio
import logging
import os.path

import discord
from plumeria import config
from plumeria.channel import Channel
from plumeria.event import bus
from plumeria.message import Message, Attachment
from plumeria.server import Server
from plumeria.transport import transports, Transport
from plumeria.util import to_mimetype
from plumeria.util.http import DefaultClientSession

discord_user = config.create("discord", "username", fallback="", comment="The Discord username to login to.")
discord_pass = config.create("discord", "password", fallback="", comment="The Discord password to login with.")

client = discord.Client()

logger = logging.getLogger(__name__)


class DiscordClient(Transport):
    id = "discord"

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate

    def __getattr__(self, item):
        return getattr(self.delegate, item)


class DiscordChannel(Channel):
    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate

    @property
    def server(self):
        return DiscordServer(self.delegate.server)

    def is_default_channel(self):
        return self.delegate.is_default_channel()

    def mention(self):
        return self.delegate.mention()

    async def send_file(self, fp, filename=None, content=None):
        return DiscordMessage(await client.send_file(self.delegate, fp, filename=filename, content=content), client)

    async def send_message(self, content, tts=False):
        return DiscordMessage(await client.send_message(self.delegate, content, tts=tts), client)

    def get_history(self, limit=100):
        logs = client.logs_from(self.delegate, limit=100)

        class HistoryWrapper:
            @asyncio.coroutine
            async def __aiter__(self):
                return self

            @asyncio.coroutine
            async def __anext__(self):
                return DiscordMessage(await logs.__anext__(), client)

        return HistoryWrapper()

    def __getattr__(self, item):
        return getattr(self.delegate, item)


class DiscordServer(Server):
    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate

    @property
    def channels(self):
        return [DiscordChannel(channel) for channel in self.delegate.channels]

    def __getattr__(self, item):
        return getattr(self.delegate, item)


class DiscordMessage(Message):
    def __init__(self, message, client):
        super().__init__()
        self.delegate = message
        self.channel = DiscordChannel(message.channel)
        self.client = client
        self.attachments = list(map(lambda o: DiscordAttachment(o), message.attachments))

    def __getattr__(self, item):
        return getattr(self.delegate, item)


class DiscordAttachment(Attachment):
    def __init__(self, data):
        super().__init__()
        self.url = data['url']
        _, ext = os.path.splitext(data['filename'])
        self.filename = data['filename']
        self.mime_type = to_mimetype(ext)

    async def read(self):
        with DefaultClientSession() as session:
            async with session.get(self.url) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    raise IOError("Did not get 200 status")

    def copy(self):
        return self


class DiscordTransport(Transport):
    def __init__(self, delegate):
        self.delegate = delegate

    @property
    def servers(self):
        return [DiscordServer(server) for server in self.delegate.servers]

    def __getattr__(self, item):
        return getattr(self.delegate, item)


@client.event
async def on_ready():
    logger.info("Logged in as {} ({})".format(client.user.name, client.user.id))
    await bus.post("discord.ready", DiscordClient(client))


@client.event
async def on_channel_delete(channel):
    await bus.post("channel.delete", DiscordChannel(channel))


@client.event
async def on_server_remove(server):
    await bus.post("server.remove", DiscordServer(server))


@client.event
async def on_message(message):
    if message.author != client.user:
        await bus.post("message", DiscordMessage(message, DiscordClient(client)))
    else:
        await bus.post("self_message", DiscordMessage(message, DiscordClient(client)))


@client.event
async def on_message_delete(message):
    await bus.post("message.delete", DiscordMessage(message, DiscordClient(client)))


@client.event
async def on_message_edit(before, after):
    await bus.post("message.edit",
                   DiscordMessage(before, DiscordClient(client)),
                   DiscordMessage(after, DiscordClient(client)))


@bus.event("init")
async def init():
    username = discord_user()
    if username != "":
        transports.register("discord", DiscordTransport(client))
        asyncio.get_event_loop().create_task(client.start(username, discord_pass()))
    else:
        logger.warning("No Discord username/password set! Not connecting to Discord...")
