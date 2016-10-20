import argparse
import logging
from functools import wraps

from plumeria.command.exception import *
from plumeria.command.manager import Command, Mapping, CommandManager, Context, CommandError
from plumeria.command.parse import Parser
from plumeria.event import bus
from plumeria.message import Response
from plumeria.transaction import tx_log
from plumeria.util.ratelimit import MessageTokenBucket, RateLimitExceeded

__all__ = ('ArgumentParser', 'commands', 'global_tokens')

logger = logging.getLogger(__name__)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(message)


commands = CommandManager(('+', '@', ';', '.', '!', '/'))
global_tokens = MessageTokenBucket(20, 12, 8, 6, fill_rate=0.25)


@bus.event("message")
async def on_message(message):
    if commands.matches_command(message.content):
        try:
            global_tokens.consume(message)
        except RateLimitExceeded as e:
            logger.warning(str(e))
            return

        response = await commands.execute(message, Context(), direct=True)
        if response:
            if not len(response.content) and not len(response.attachments):
                response = Response("\N{WARNING SIGN} Command returned empty text as a response.")
            tx_log.add_response(message, await message.respond(response))


def channel_only(f):
    @wraps(f)
    async def wrapper(message, *args, **kwargs):
        if not message.channel.is_private:
            return await f(message, *args, **kwargs)
        else:
            raise CommandError("You can only use this on a server, not in a private message")

    return wrapper
