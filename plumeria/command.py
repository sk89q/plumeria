import argparse
import inspect
import logging

import re
from collections import namedtuple
from functools import wraps

from io import StringIO
from .message import ProxyMessage, Response
from .event import bus
from .util.ratelimit import MessageTokenBucket, RateLimitExceeded

__all__ = ('CommandManager',)

DESCRIPTION_PATTERN = re.compile("^([^\r\n]*)")
COMMAND_TOKENS_PATTERN = re.compile("[ \\r\\n\\t]")

logger = logging.getLogger(__name__)


class CommandError(Exception):
    """Raised on any command processing error."""


class ArgumentError(CommandError):
    pass


class AuthorizationError(Exception):
    """Raised when the user does not have sufficient permissions."""


class ComplexityError(Exception):
    """Raised if a command is too complex to complete completely."""


class Command:
    def __init__(self, executor, cost=1.0, category=None, description=None, help=None):
        self.executor = executor
        self.cost = cost
        self.category = category
        if description:
            self.description = description
        else:
            doc = inspect.getdoc(executor)
            if doc:
                self.description = DESCRIPTION_PATTERN.match(doc).group(1)
            else:
                self.description = "No information."
        if help:
            self.help = help
        else:
            self.help = inspect.getdoc(executor)
        self.server_admins_only = hasattr(executor, "server_admins_only")
        self.owners_only = hasattr(executor, "owners_only")

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Context:
    def __init__(self, max_cost=10):
        self.total = 0
        self.max_cost = max_cost

    def consume(self, cost):
        if self.total + cost > self.max_cost:
            raise ComplexityError("{} + {} > {}".format(self.total, cost, self.max_cost))
        self.total += cost


Mapping = namedtuple("Mapping", "aliases command")


class PrefixTree:
    def __init__(self):
        self.content = None
        self.children = {}


class CommandManager:
    def __init__(self, prefixes):
        self.commands = PrefixTree()
        self.mappings = []
        self.interceptors = []
        self.enumerators = []
        self.prefixes = prefixes

    async def get_mappings(self, server_id=None):
        mappings = self.mappings[:]
        for enumerator in self.enumerators:
            mappings.extend(await enumerator(server_id=server_id))
        return mappings

    def register(self, *aliases, **kwargs):
        """
        Register a new command. Command aliases are case-insensitive.

        :param aliases: a list of aliases
        :param cost: a cost that is used to prevent piping too many commands in
                     one single statement
        :param category: category in title case
        :param description: a short description of the command
        :param help: a long RST-formatted help text
        """
        def decorator(f):
            command = Command(f, **kwargs)
            for alias in aliases:
                root = self.commands
                alias_lower = alias.lower()
                prefixes = alias_lower.split(" ")
                while len(prefixes):
                    prefix = prefixes.pop(0)
                    if prefix not in root.children:
                        root.children[prefix] = PrefixTree()
                    root = root.children[prefix]
                if root.content:
                    raise Exception("{} is already registered to {} -- cannot register to {}"
                                    .format(alias.lower(), root.content.executor, f))
                root.content = command
            self.mappings.append(Mapping(aliases, command))
            return f

        return decorator

    def enumerator(self, f):
        self.enumerators.append(f)
        return f

    def intercept(self, f):
        self.interceptors.append(f)
        return f

    def matches_command(self, s):
        prefix_test = s.lower()
        for prefix in self.prefixes:
            if prefix_test.startswith(prefix):
                return True
        return False

    async def execute_unprefixed(self, message, context):
        # single prefix stuff for interceptors
        split = message.content.split(" ", 1)
        name = split[0].lower()
        split_message = ProxyMessage(message)
        split_message.content = split[1] if len(split) > 1 else ""

        # check with interceptors
        for interceptor in self.interceptors:
            result = await interceptor(split_message, name, context)
            if result:
                return result

        # check registered commands
        root = self.commands
        content = message.content
        while True:
            split = COMMAND_TOKENS_PATTERN.split(content, 1)
            name = split[0].strip().lower()
            if name in root.children:
                root = root.children[name]
                content = split[1] if len(split) > 1 else ""
            else:
                break

        if root.content:
            command = root.content
            message.content = content
            context.consume(command.cost)
            result = await command.executor(message)
            if result is None:
                return None
            elif isinstance(result, Response):
                return result
            elif isinstance(result, str):
                return Response(result)
            else:
                raise Exception("The command {} did not return a Response object or a str".format(str(command)))

    async def execute_prefixed(self, message, context, expect_prefix=True):
        prefix_test = message.content.lower()

        for prefix in self.prefixes:
            if prefix_test.startswith(prefix):
                message = ProxyMessage(message)
                message.content = message.content[len(prefix):].lstrip()
                return await self.execute_unprefixed(message, context)

        if not expect_prefix:
            return await self.execute_unprefixed(message, context)

    async def execute(self, message, context, expect_prefix=True):
        if expect_prefix:
            prefix_test = message.content.lower()
            found = False
            for prefix in self.prefixes:
                if prefix_test.startswith(prefix):
                    found = True
                    break
            if not found:
                return

        try:
            input = None
            for command in self._split_piped(message.content):
                message = ProxyMessage(message)
                if input:
                    command = command + " " + input.content
                    message.attachments = input.attachments
                message.content = command
                input = await self.execute_prefixed(message, context, expect_prefix=False)
            return input
        except AuthorizationError as e:
            await message.respond("error: Whoops -- you can't use this.")
        except ComplexityError as e:
            await message.respond("error: Your command was too complex to handle. Calm down.")
        except CommandError as e:
            await message.respond("error: {}".format(str(e)))
        except RateLimitExceeded as e:
            await message.respond("error: Your command is hitting a rate limit. Try again later.")
        except Exception as e:
            logger.warning("Command raised an exception for '{}'".format(message.content), exc_info=True)
            await message.respond("error: An unexpected error occurred.")

    def _split_piped(self, s):
        escaping = False
        parts = [StringIO()]
        for i in range(0, len(s)):
            if escaping:
                if s[i] != "|":
                    parts[len(parts) - 1].write("^")
                parts[len(parts) - 1].write(s[i])
                escaping = False
            elif s[i] == "^":
                escaping = True
            elif s[i] == "|":
                parts.append(StringIO())
            else:
                parts[len(parts) - 1].write(s[i])
        parts = map(lambda x: x.getvalue().strip(), parts)
        parts = filter(lambda x: len(x), parts)
        return list(parts)


class ArgumentParserError(Exception):
    pass


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

        response = await commands.execute(message, Context())
        if response:
            await message.respond(response)


def channel_only(f):
    @wraps(f)
    async def wrapper(message, *args, **kwargs):
        if not message.channel.is_private:
            return await f(message, *args, **kwargs)
        else:
            raise CommandError("You can only use this on a server, not in a private message")

    return wrapper
