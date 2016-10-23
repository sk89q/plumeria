"""A list of common configuration options that might be used by plugins."""
from functools import wraps

from plumeria import config
from plumeria.command import CommandError
from plumeria.config.types import boolstr, dateformatstr
from plumeria.core.scoped_config import scoped_config

allow_games = config.create("common", "allow_games", type=boolstr, fallback=False,
                            comment="Whether to allow game functions",
                            scoped=True, private=False)

nsfw = config.create("common", "nsfw", type=boolstr, fallback=False, comment="Whether to allow NSFW functions",
                     scoped=True, private=False)

short_date_time_format = config.create("common", "date_time_short", type=dateformatstr,
                                       fallback="%b %m, %Y %I:%M %p %Z", comment="Short date and time format",
                                       scoped=True, private=False)

config.add(allow_games)
config.add(nsfw)
config.add(short_date_time_format)


def games_allowed_only(f):
    @wraps(f)
    async def wrapper(message, *args, **kwargs):
        if not scoped_config.get(allow_games, message.channel):
            raise CommandError(
                "Games aren't allowed here! Enable games by setting the `common/allow_games` config setting to `yes` for the channel or server.")
        if not message.channel.is_private:
            return await f(message, *args, **kwargs)

    return wrapper
