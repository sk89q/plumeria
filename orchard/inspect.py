"""Get details about users and servers, like avatar, and so on."""

from colour import Color

from plumeria.command import commands, channel_only, CommandError
from plumeria.config.common import short_date_time_format
from plumeria.core.scoped_config import scoped_config
from plumeria.message.mappings import build_mapping
from plumeria.transport import User


def find_user(message):
    query = message.content.strip()
    if len(query):
        user = message.channel.transport.resolve_user(query, hint=message.mentions, domain=message.channel.members)
    else:
        user = message.author
    if not user:
        raise CommandError("User was not found.")
    return user


@commands.create('avatar', 'user avatar', category='Inspection')
async def avatar(message):
    """
    Gets the URL of a user's avatar or the avatar of the calling user if no username
    is provided.

    Example::

        /avatar @bob#0000
    """
    user = find_user(message)
    avatar = user.avatar_url
    if len(avatar):
        return avatar
    else:
        raise CommandError("That user has no avatar.")


@commands.create('user', 'user info', category='Inspection')
async def user_info(message):
    """
    Get information about a user:

    Example::

        /user @bob#0000
    """
    user = find_user(message)  # type: User

    entries = [
        ('Name', user.name),
        ('Display Name', user.display_name),
        ('ID', user.id),
        ('Discriminator', user.discriminator),
        ('Bot', "Yes" if user.bot else "No"),
        ('Creation Time', user.created_at.strftime(scoped_config.get(short_date_time_format, message.channel))),
    ]

    if hasattr(user, 'joined_at'):
        entries += [
            ('Status', user.status),
            ('Game', user.game.name if user.game else "None"),
            ('Color', Color(red=user.colour.r / 255, green=user.colour.g / 255, blue=user.colour.b / 255).hex),
        ]

    return build_mapping(entries)


@commands.create('icon', 'server icon', category='Inspection')
@channel_only
async def icon(message):
    """
    Gets the URL of the server icon.

    Example::

        /icon
    """
    icon = message.channel.server.icon_url
    if len(icon):
        return icon
    else:
        raise CommandError("That server has no icon.")


@commands.create('server', 'server info', category='Inspection')
@channel_only
async def server_info(message):
    """
    Get information about the current server:

    Example::

        /server
    """
    server = message.channel.server

    entries = [
        ('Name', server.name),
        ('ID', server.id),
        ('Emoji Count', len(server.emojis)),
        ('Region', server.region),
        ('AFK Timeout', server.afk_timeout),
        ('AFK Channel', server.afk_channel.name if server.afk_channel else "None"),
        ('Owner', "{} [{}#{}] ({})".format(server.owner.display_name, server.owner.name, server.owner.discriminator,
                                           server.owner.id) if server.owner else None),
        ('MFA Level', server.mfa_level),
        ('Verification Level', server.verification_level),
        ('Default Channel', server.default_channel.name),
        ('Member Count', server.member_count),
        ('Creation Time', server.created_at.strftime(scoped_config.get(short_date_time_format, message.channel))),
    ]

    return build_mapping(entries)


def setup():
    commands.add(avatar)
    commands.add(user_info)
    commands.add(icon)
    commands.add(server_info)
