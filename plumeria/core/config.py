"""Commands to set configuration options per-server and per-channel."""

import re
from typing import Union

from plumeria import config
from plumeria.command import channel_only, commands, CommandError
from plumeria.config import Setting
from plumeria.core.scoped_config import scoped_config, ScopedValue
from plumeria.message import Message
from plumeria.message.mappings import build_mapping
from plumeria.perms import server_admins_only
from plumeria.transport import Channel
from plumeria.transport import Server
from plumeria.util.format import escape_markdown

KEY_PATTERN = re.compile("^([^/]+)/(.*)$")


def value_str(s):
    return str(s) if s is not None else "\N{NEGATIVE SQUARED CROSS MARK}"


def find_setting(setting_key, non_private_only=True):
    # make sure that the key name is section/name
    m = KEY_PATTERN.match(setting_key)
    if not m:
        raise CommandError("The setting name needs to be 'section/name'")

    # find setting
    try:
        setting = config.get_setting(m.group(1), m.group(2))
    except KeyError:
        raise CommandError("No such setting **{}** exists".format(setting_key))

    if not setting.scoped:
        raise CommandError("The setting **{}** can't be overridden for a server or channel".format(setting_key))

    if non_private_only and setting.private:
        raise CommandError(
            "The configuration variable **{}/{}** is private and can only be set".format(setting.section, setting.key))

    return setting


async def do_set(message, scope: Union[Server, Channel], scope_name: str):
    parts = message.content.split(" ", 1)
    if len(parts) != 2:
        raise CommandError("<name> <value>")

    setting_key, raw_value = parts
    setting = find_setting(setting_key, non_private_only=False)

    try:
        await scoped_config.put(setting, scope, raw_value)
        return "Set **{}** to `{}` on {}".format(setting_key, escape_markdown(raw_value), scope_name)
    except Exception as e:
        raise CommandError("Could not set **{}**: {}".format(setting_key, str(e)))


async def do_unset(message, scope: Union[Server, Channel], scope_name: str):
    parts = message.content.strip().split(" ", 1)
    if len(parts) != 1:
        raise CommandError("<name>")

    setting_key = parts[0]
    setting = find_setting(setting_key, non_private_only=False)

    try:
        await scoped_config.delete(setting, scope)
        return "Deleted **{}** on {}".format(setting_key, scope_name)
    except Exception as e:
        raise CommandError("Could not delete **{}**: {}".format(setting_key, str(e)))


def map_sv(sv: ScopedValue):
    setting = config.get_setting(sv.section, sv.key)
    if setting.private:
        return "**{}/{}**: (private)".format(sv.section, sv.key, sv.value)
    else:
        return "**{}/{}**: {}".format(sv.section, sv.key, sv.value)


def map_setting(setting: Setting):
    return "**{}/{}:** {} (value: {})".format(setting.section, setting.key, escape_markdown(setting.comment),
                                              value_str(setting()) if not setting.private else "(private)")


@commands.create('set', 'set server', 'set s', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def set_server(message: Message):
    """
    Sets a server-wide configuration variable. Will override the global configuration.

    Example::

        /set server common/nsfw false
    """
    return await do_set(message, message.channel.server, "the server ({})".format(message.channel.server.name))


@commands.create('set channel', 'set chan', 'set c', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def set_channel(message: Message):
    """
    Sets a configuration variable for the current channel. Will override the server configuration (if any)
    and the global configuration.

    Example::

        /set chan common/nsfw false
    """
    return await do_set(message, message.channel, message.channel.mention)


@commands.create('unset', 'unset server', 'unset s', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def unset_server(message: Message):
    """
    Removes a server-wide configuration variable.

    Example::

        /unset server common/nsfw false
    """
    return await do_unset(message, message.channel.server, "the server ({})".format(message.channel.server.name))


@commands.create('unset channel', 'unset chan', 'unset c', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def unset_channel(message: Message):
    """
    Removes a configuration variable for the current channel.

    Example::

        /unset chan common/nsfw false
    """
    return await do_unset(message, message.channel, message.channel.mention)


@commands.create('config get', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def get(message: Message):
    """
    Get an effective configuration value.

    Example::

        /config get common/nsfw
    """
    query = message.content.strip()
    if not len(query):
        raise CommandError("A configuration name in the form of `section/key` needs to be provided")
    setting = find_setting(query, non_private_only=True)
    return str(scoped_config.get(setting, message.channel))


@commands.create('config info', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def info(message: Message):
    """
    Get the global, server, and channel value for a configuration setting.

    Example::

        /config info common/nsfw
    """
    query = message.content.strip()
    if not len(query):
        raise CommandError("A configuration name in the form of `section/key` needs to be provided")

    setting = find_setting(query, non_private_only=True)
    global_value = setting()
    server_value = scoped_config.get_server(setting, message.server)
    channel_value = scoped_config.get_channel(setting, message.channel)
    effective_value = scoped_config.get(setting, message.channel)

    items = [
        ('Global', value_str(global_value)),
        ('Server', value_str(server_value)),
        ('Channel', value_str(channel_value)),
        ('Effective', value_str(effective_value)),
    ]

    return build_mapping(items)


@commands.create('config list', 'configs', 'confs', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def list(message: Message):
    """
    Get a list of configuration variables that have been set for this channel as well
    as on the server that the channel is in.
    """
    server_results = "\n".join(map(map_sv, scoped_config.get_all_server(message.server)))
    channel_results = "\n".join(map(map_sv, scoped_config.get_all_channel(message.channel)))
    return "__Server:__\n{}\n\n__{}:__\n{}".format(
        server_results if len(server_results) else "none set",
        message.channel.mention,
        channel_results if len(channel_results) else "none set",
    )


@commands.create('config defaults', cost=4, category='Configuration')
@channel_only
@server_admins_only
async def list_defaults(message: Message):
    """
    Get a list of configuration variables that can be set.
    """
    settings = config.get_settings(scoped=True)
    if len(settings):
        items = [(setting.section + "/" + setting.key, '{} (value: {})'.format(setting.comment, setting.fallback)) for
                 setting in settings]
        return build_mapping(items)
    else:
        raise CommandError("No preferences exist to be set.")


def setup():
    commands.add(set_server)
    commands.add(set_channel)
    commands.add(unset_server)
    commands.add(unset_channel)
    commands.add(get)
    commands.add(info)
    commands.add(list)
    commands.add(list_defaults)
