import asyncio
import logging
import os.path
import discord
from plumeria import config
from plumeria.channel import Channel
from plumeria.event import bus
from plumeria.message import Message, Attachment
from plumeria.util import to_mimetype
from plumeria.util.http import DefaultClientSession

discord_user = config.create("discord", "username", comment="The Discord username to login to.")
discord_pass = config.create("discord", "password", comment="The Discord password to login with.")

client = discord.Client()

logger = logging.getLogger(__name__)


class DiscordChannel(Channel):
    def __init__(self, delegate):
        kwargs = {key: getattr(delegate, key) for key in (
            "name", "server", "id", "topic", "is_private", "position", "type", "bitrate", "voice_members", "user_limit",
            "is_default", "mention", "created_at")}
        super().__init__(**kwargs)
        self.delegate = delegate

    async def send_file(self, fp, filename=None, content=None):
        return await client.send_file(self.delegate, fp, filename=filename, content=content)

    async def send_message(self, content, tts=False):
        return await client.send_message(self.delegate, content, tts=tts)

    def get_history(self, limit=100):
        logs = client.logs_from(self.delegate, limit=100)

        class HistoryWrapper:
            @asyncio.coroutine
            async def __aiter__(self):
                return self

            @asyncio.coroutine
            async def __anext__(self):
                return DiscordMessage(await logs.__anext__())

        return HistoryWrapper()


class DiscordMessage(Message):
    def __init__(self, message):
        attachments = list(map(lambda o: DiscordAttachment(o), message.attachments))
        self.discord_channel = message.channel
        super().__init__(DiscordChannel(message.channel),
                         message.author, message.content, message.embeds, attachments,
                         message.timestamp, message.edited_timestamp, message.tts)


class DiscordAttachment(Attachment):
    def __init__(self, data):
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


@client.event
async def on_ready():
    logger.info("Logged in as {} ({})".format(client.user.name, client.user.id))
    await bus.post("discord.ready", client)


@client.event
async def on_channel_delete(channel):
    await bus.post("channel.delete", DiscordChannel(channel))


@client.event
async def on_server_remove(server):
    await bus.post("server.remove", server)


@client.event
async def on_message(message):
    if message.author != client.user:
        await bus.post("message", DiscordMessage(message))
    else:
        await bus.post("self_message", DiscordMessage(message))


@bus.event("init")
async def init():
    await client.start(discord_user(), discord_pass())
