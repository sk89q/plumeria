"""Connect the bot to Discord."""

import asyncio
import inspect
import logging
import os.path
import re
from enum import Enum
from typing import Sequence, Optional

import discord
from discord import Client
from discord import Permissions
from discord import Server as _Server, Channel as _Channel, PrivateChannel as _PrivateChannel, Member as _Member, \
    Message as _Message, User as _User
from discord import VoiceClient

from plumeria import config
from plumeria.event import bus
from plumeria.message import Message, Attachment
from plumeria.plugin import PluginSetupError
from plumeria.transport import Channel, Server
from plumeria.transport import User
from plumeria.transport import transports, Transport
from plumeria.transport.transport import ForbiddenError
from plumeria.util import to_mimetype
from plumeria.util.http import DefaultClientSession

discord_user = config.create("discord", "username", fallback="", comment="The Discord username to login to")
discord_pass = config.create("discord", "password", fallback="", comment="The Discord password to login with")
discord_token = config.create("discord", "token", fallback="",
                              comment="The Discord token to login with (overrides password login if set)")

logger = logging.getLogger(__name__)

DICT_VALUES = {}.values().__class__
MENTION_RE = re.compile("@?([^<> #]+)(?:#([0-9]{4}))?")


def _wrap(o, transport):
    if isinstance(o, list) or isinstance(o, DICT_VALUES):
        return [_wrap(item, transport) for item in o]
    elif isinstance(o, tuple):
        return tuple([_wrap(item, transport) for item in o])
    elif isinstance(o, Client):
        return transport
    elif isinstance(o, _Server):
        return DiscordServer(o, transport)
    elif isinstance(o, _Channel):
        return DiscordChannel(o, transport)
    elif isinstance(o, _PrivateChannel):
        return DiscordChannel(o, transport)
    elif isinstance(o, _Message):
        return DiscordMessage(o, transport)
    elif isinstance(o, _Member):
        return DiscordWrapper(o, transport)
    elif isinstance(o, _User):
        return DiscordWrapper(o, transport)
    elif isinstance(o, VoiceClient):
        return DiscordWrapper(o, transport)
    elif isinstance(o, Enum):
        return str(o)

    return o


class DiscordWrapper:
    def __init__(self, delegate, transport):
        super().__init__()
        self.transport = transport  # type: DiscordTransport
        self.delegate = delegate

    def voice_client_in(self, server):
        return self._wrap(self.delegate.voice_client_in(server))

    def _wrap(self, object):
        return _wrap(object, self.transport)

    def __getattr__(self, item):
        attr = getattr(self.delegate, item)

        if inspect.iscoroutinefunction(attr) or hasattr(attr,
                                                        "_is_coroutine") and attr._is_coroutine or inspect.iscoroutine(
            attr):
            async def wrapper(*args, **kwargs):
                return self._wrap(await attr(*args, **kwargs))

            return wrapper() if inspect.iscoroutine(attr) else wrapper
        elif inspect.isgeneratorfunction(attr) or inspect.isgenerator(attr):
            def wrapper(*args, **kwargs):
                for entry in attr(*args, **kwargs):
                    yield self._wrap(entry)

            return wrapper if inspect.isgeneratorfunction(attr) else wrapper()
        elif inspect.isfunction(attr):
            def wrapper(*args, **kwargs):
                return self._wrap(attr(*args, **kwargs))

            return wrapper
        else:
            return self._wrap(attr)

    def __str__(self):
        return str(self.delegate)

    def __repr__(self):
        return repr(self.delegate)

    def __hash__(self):
        return self.delegate.__hash__()

    def __eq__(self, other):
        if isinstance(other, DiscordWrapper):
            other = other.delegate
        return self.delegate.__eq__(other)


class DiscordTransport(DiscordWrapper, Transport):
    def __init__(self, delegate):
        super().__init__(delegate, self)
        self.id = 'discord'

    def resolve_user(self, q, hint: Optional[Sequence[User]] = None, domain: Optional[Sequence[User]] = None):
        m = MENTION_RE.search(q)
        if m:
            name_id = m.group(1)
            discrim = m.group(2)

            if hint:
                for user in hint:
                    if discrim and discrim != str(user.discriminator):
                        continue
                    if name_id == str(user.id) or name_id.lower() == user.name.lower():
                        return user

            if not domain:
                domain = self.get_all_members()

            for user in domain:
                if discrim and discrim != str(user.discriminator):
                    continue
                if name_id == str(user.id) or name_id.lower() == user.name.lower():
                    return user
        return None

    async def start_private_message(self, user):
        return self._wrap(await self.delegate.start_private_message(user.delegate))

    async def edit_profile(self, **fields):
        return await self.delegate.edit_profile(password=discord_pass(), **fields)

    @property
    def servers(self):
        return [self._wrap(o) for o in self.delegate.servers]


class DiscordChannel(DiscordWrapper, Channel):
    async def send_file(self, fp, filename=None, content=None):
        return await self.transport.send_file(self.delegate, fp, filename=filename, content=content)

    async def send_message(self, content, tts=False, embed=None):
        return await self.transport.send_message(self.delegate, content, tts=tts, embed=embed)

    @property
    def multiple_participants(self):
        return self.type in ('text', 'voice', 'group')

    @property
    def server(self):
        if hasattr(self.delegate, 'server'):
            return self._wrap(self.delegate.server)
        else:
            return None

    @property
    def members(self):
        if self.is_private:
            for user in self.recipients:
                yield user
        else:
            for member in self.server.members:
                if self.permissions_for(member).read_messages:
                    yield member

    def get_history(self, limit=100):
        logs = self.transport.logs_from(self.delegate, limit=limit)
        transport = self.transport

        class HistoryWrapper:
            @asyncio.coroutine
            async def __aiter__(self):
                return self

            @asyncio.coroutine
            async def __anext__(self):
                return DiscordMessage(await logs.__anext__(), transport)

        return HistoryWrapper()


class DiscordServer(DiscordWrapper, Server):
    async def create_custom_emoji(self, name, image):
        try:
            return await self.transport.create_custom_emoji(self.delegate, name=name, image=image)
        except discord.errors.Forbidden as e:
            raise ForbiddenError(str(e))

    async def delete_custom_emoji(self, emoji):
        try:
            return await self.transport.delete_custom_emoji(emoji)
        except discord.errors.Forbidden as e:
            raise ForbiddenError(str(e))

    async def update(self, **kwargs):
        return await self.transport.edit_server(self.delegate, **kwargs)


class DiscordMessage(DiscordWrapper, Message):
    @property
    def attachments(self):
        return list(map(lambda o: DiscordAttachment(o), self.delegate.attachments))


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


client = discord.Client()
transport = DiscordTransport(client)


def setup():
    config.add(discord_user)
    config.add(discord_pass)
    config.add(discord_token)

    if (not len(discord_user()) or not len(discord_pass())) and not len(discord_token()):
        raise PluginSetupError("This plugin requires a username and password or login token from "
                               "https://discordapp.com. Registration is free.")

    @client.event
    async def on_ready():
        logger.info("Discord logged in as {} ({})".format(client.user.name, client.user.id))
        await bus.post("transport.ready", transport)
        for server in transport.servers:
            await bus.post("server.ready", server)
        if discord_token():
            app_info = await client.application_info()
            logger.info("Use this link to add the bot to a server: {}".format(discord.utils.oauth_url(app_info.id, Permissions.all())))

    @client.event
    async def on_channel_update(before, after):
        await bus.post("channel.before", _wrap(before, transport))
        await bus.post("channel.after", _wrap(after, transport))

    @client.event
    async def on_member_join(member):
        await bus.post("server.member.join", _wrap(member, transport))

    @client.event
    async def on_member_update(before, after):
        await bus.post("server.member.update", _wrap(before, transport), _wrap(after, transport))

    @client.event
    async def on_channel_delete(channel):
        await bus.post("channel.delete", _wrap(channel, transport))

    @client.event
    async def on_server_join(server):
        wrapped = _wrap(server, transport)
        await bus.post("server.join", wrapped)
        await bus.post("server.ready", wrapped)

    @client.event
    async def on_server_update(before, after):
        await bus.post("server.update", _wrap(before, transport), _wrap(after, transport))

    @client.event
    async def on_server_remove(server):
        wrapped = _wrap(server, transport)
        await bus.post("server.unready", wrapped)
        await bus.post("server.remove", wrapped)

    @client.event
    async def on_server_available(server):
        await bus.post("server.available", _wrap(server, transport))

    @client.event
    async def on_server_unavailable(server):
        await bus.post("server.unavailable", _wrap(server, transport))

    @client.event
    async def on_group_join(server):
        await bus.post("server.available", _wrap(server, transport))

    @client.event
    async def on_group_remove(server):
        await bus.post("server.unavailable", _wrap(server, transport))

    @client.event
    async def on_message(message):
        if message.author != client.user:
            await bus.post("message", _wrap(message, transport))
        else:
            await bus.post("self_message", _wrap(message, transport))

    @client.event
    async def on_message_delete(message):
        await bus.post("message.delete", _wrap(message, transport))

    @client.event
    async def on_message_edit(before, after):
        await bus.post("message.edit",
                       _wrap(before, transport),
                       _wrap(after, transport))

    @bus.event("init")
    async def init():
        token = discord_token()
        if len(token):
            transports.register(transport.id, transport)
            asyncio.get_event_loop().create_task(client.start(token))
        else:
            username = discord_user()
            if username != "":
                transports.register(transport.id, transport)
                asyncio.get_event_loop().create_task(client.start(username, discord_pass()))
            else:
                logger.warning("No Discord username/password set! Not connecting to Discord...")
