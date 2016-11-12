"""Classes to keep track of and dispatch commands."""

import inspect
import logging
import re
from io import StringIO
from typing import Dict, List, Sequence, Optional, Callable

from plumeria.command.parse import Parser
from plumeria.message import ProxyMessage, Response
from plumeria.util.ratelimit import RateLimitExceeded
from .exception import *

__all__ = ('Command', 'CommandManager', 'split_piped', 'interpolate')

DESCRIPTION_PATTERN = re.compile("^([^\r\n]*)")
COMMAND_TOKENS_PATTERN = re.compile("[ \\r\\n\\t]")

logger = logging.getLogger(__name__)


def split_piped(s: str) -> List[str]:
    """
    Splits a into a list of commands split by vertical bar symbols.

    Parameters
    ----------
    s : str
        The command string to parse

    Returns
    -------
    List[str]
        A list of commands

    """
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
    if escaping:
        parts[len(parts) - 1].write("^")
    parts = map(lambda x: x.getvalue().strip(), parts)
    parts = filter(lambda x: len(x), parts)
    return list(parts)


def interpolate(s: str, registers: Dict) -> str:
    """
    Interpolates variables in a string with values from a supplied dictionary of registers.

    The parser is very lax and will not interpolate variables that don't exist, as users
    may not be intending to interpolate a variable when they type the hash character.
    The hash symbols can be escaped with a caret (^), but if a caret is placed before
    a character that doesn't need escaping (another caret or a hash character), then
    the escape character acts as a normal character (nothing is removed or replaced).

    Parameters
    ----------
    s : str
        The string to interpolate
    registers : Dict[str, Message]
        A mapping of variable names to messages

    Returns
    -------
    str
        A new string with interpolated values

    """
    escaping = False
    variable_mode = False
    buffer = StringIO()
    variable_buffer = StringIO()
    for i in range(0, len(s)):
        if escaping:
            if s[i] != "#":
                buffer.write("^")
            buffer.write(s[i])
            escaping = False
        elif variable_mode:
            if s[i] == "#":
                name = variable_buffer.getvalue()
                if name in registers:
                    buffer.write(registers[name].content)
                else:
                    buffer.write("#")
                    buffer.write(name)
                    buffer.write("#")
                variable_buffer = StringIO()
                variable_mode = False
            elif s[i] != " ":
                variable_buffer.write(s[i])
            else:  # invalid variable name
                buffer.write("#")
                buffer.write(variable_buffer.getvalue())
                buffer.write(s[i])
                variable_buffer = StringIO()
                variable_mode = False
        elif s[i] == "^":
            escaping = True
        elif s[i] == "#":
            variable_mode = True
        else:
            buffer.write(s[i])
    if escaping:
        buffer.write("^")
    if len(variable_buffer.getvalue()):
        buffer.write("#")
        buffer.write(variable_buffer.getvalue())
    return buffer.getvalue()


class Command:
    """
    Stores metadata about a command. This class does not store aliases, however.
    See :class:`Mapping` to see where aliases are stored in association with a command.

    Instances of this class are created by the :class:`CommandManager`.

    Attributes
    ----------
    executor : Callable
        The function to call when the command is invoked.
    cost : float
        The cost of invoking the command, where the default is 1.0.
    category : str
        The name of the category that the command should appear in on the help page
    description : str
        A short description of the command, in restructedText
    help : str
        A long help version of the command, in restructuredText
    params : Optional[List[Parameter]]
        A list of parameters to use to parse arguments that are to be passed to the executor

    """

    def __init__(self, executor, cost=1.0, category=None, description=None, help=None, params=None):
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
        self.params = params
        self.server_admins_only = hasattr(executor, "server_admins_only")
        self.owners_only = hasattr(executor, "owners_only")

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Mapping:
    """
    Stores a mapping of aliases and commands together.

    Attributes
    ----------
    aliases : Sequence[str]
        A sequence of aliases
    command : :class:`Command`
        The command

    """
    __slots__ = ('aliases', 'command')

    def __init__(self, aliases: Sequence[str], command: Command):
        self.aliases = aliases
        self.command = command

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class Context:
    """
    A context exists during the execution of a command or command chain. A context is currently
    used to sum up the cost of executing the current command.

    Instances of this class are created by the :class:`CommandManager`.

    Attributes
    ----------
    total : float
        How much cost has been used up
    max_cost : float
        The maximum total cost of the command

    """

    def __init__(self, max_cost=10):
        self.total = 0
        self.max_cost = max_cost

    def consume(self, cost: float):
        """
        Consumes a token with the given cost.

        Parameters
        ----------
        cost : float
            The cost to consume

        Raises
        ------
        ComplexityError
            Raised if command execution should halt because the max cost has been reached

        """
        if self.total + cost > self.max_cost:
            raise ComplexityError("{} + {} > {}".format(self.total, cost, self.max_cost))
        self.total += cost

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


class PrefixTree:
    """A simple trie to store the command hierarchy."""

    def __init__(self):
        self.content = None
        self.children = {}


class CommandManager:
    """
    Manages a list of registered commands and dispatches commands.

    Commands can be registered using :method:`register`.

    """

    def __init__(self, prefixes):
        self.commands = PrefixTree()
        self.mappings = []
        self.interceptors = []
        self.enumerators = []
        self.prefixes = prefixes
        self.parser = Parser()

    async def get_mappings(self, server_id: Optional[str] = None) -> Sequence[Mapping]:
        """
        Fetch a list of command mappings.

        Parameters
        ----------
        server_id : Optional[str]
            The server ID to get commands for (relevant for server-specific commands)

        Returns
        -------

        """
        mappings = self.mappings[:]
        for enumerator in self.enumerators:
            mappings.extend(await enumerator(server_id=server_id))
        return mappings

    def add(self, f):
        """
        Add a command to the manager.

        Parameters
        ----------
        f : Callable
            A function that has been passed through :method:`create`

        Returns
        -------
        Callable
            The supplied callable

        """
        for alias in f.command_aliases:
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
            root.content = f.command
        command_mapping = Mapping(f.command_aliases, f.command)
        self.mappings.append(command_mapping)
        return f

    def create(self, *aliases: Sequence[str], **kwargs):
        """
        A decorator to create a new command. Command aliases are case-insensitive.

        Commands still have to be later registered using :method:`register`().

        Example of registering a command via decorator:

        .. code-block: python

            @commands.register("search", category="Search", params=[Text('query')])
            async def search(message, query):
                raise CommandError("not implemented")

        Aliases may have spaces in them to create psuedo-subcommands.

        The first argument to the function when the command is called with be the
        :class:`Message` object. There may be additional arguments if some
        parameters are registered with the command.

        Type hinting on the function will not be used, primarily because it is not specific
        enough.

        Parameters
        ----------
        *aliases : Sequence[str]
            A list of aliases
        cost : float
            The cost of invoking the command, where the default is 1.0.
        category : str
            The name of the category that the command should appear in on the help page
        description : str
            A short description of the command, in restructedText
        help : str
            A long help version of the command, in restructuredText
        params : Optional[List[Parameter]]
            A list of parameters to use to parse arguments that are to be passed to the executor

        """

        def decorator(f):
            f.command = Command(f, **kwargs)
            f.command_aliases = aliases
            return f

        return decorator

    def enumerator(self, f: Callable) -> Callable:
        """Adds a new enumerator. Enumerators are used to fill out the help page."""
        self.enumerators.append(f)
        return f

    def intercept(self, f: Callable) -> Callable:
        """Adds a new interceptor. Interceptors can be used to create on-the-fly custom commands."""
        self.interceptors.append(f)
        return f

    def matches_command(self, s):
        """
        Check if the given message would likely trigger a command.

        Parameters
        ----------
        s : str
            The text message

        Returns
        -------
        bool
            Whether the command would likely trigger a command

        """
        prefix_test = s.lower()
        for prefix in self.prefixes:
            if prefix_test.startswith(prefix):
                return True
        return False

    async def _execute_unprefixed(self, message, context: Context) -> Response:
        """
        Internal function to execute a single command that has no command prefix in front
        of it (it may have already been stripped out).

        This function does the heavy work of actually executing the command.

        Parameters
        ----------
        message : :class:`Message`
            The message
        context : :class:`Context`
            Current execution context

        Returns
        -------
        Awaitable[Optional[:class:`Response`]]
            A response, or None if the command was not found

        """
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

            # parse parameters into arguments
            if command.params:
                args = self.parser.parse(message.content, command.params)
            else:
                args = {}

            result = await command.executor(message, **args)
            if result is None:
                return Response()
            elif isinstance(result, Response):
                return result
            elif isinstance(result, str):
                return Response(result)
            else:
                raise Exception("The command {} did not return a Response object or a str".format(str(command)))

    async def _execute_prefixed(self, message, context, expect_prefix=True):
        """
        Internal function to execte a single command that may or may not have a command prefix.

        Parameters
        ----------
        message : :class:`Message`
            The message
        context : :class:`Context`
            Current execution context
        expect_prefix: : bool
            If true and no command prefix is provided, then no command will be executed and None will be returned

        Returns
        -------
        Awaintable[Optional[:class:`Response`]]
            A response, or None if the command was not found

        """
        prefix_test = message.content.lower()

        for prefix in self.prefixes:
            if prefix_test.startswith(prefix):
                message = ProxyMessage(message)
                message.content = message.content[len(prefix):].lstrip()
                return await self._execute_unprefixed(message, context)

        if not expect_prefix:
            return await self._execute_unprefixed(message, context)

    async def execute(self, message, context, expect_prefix=True, direct=False):
        """
        Executes a command. The command may or may not have prefixes and there may actually be several
        commands being piped together.

        All non-command error exceptions are wrapped by a :class:`CommandError`.

        Parameters
        ----------
        message : :class:`Message`
            The message
        context : :class:`Context`
            Current execution context
        expect_prefix : bool
            If true and no command prefix is provided, then no command will be executed and None will be returned
        direct : bool
            Whether the command being executed was directly typed by the user executing the command not from some
            alias set by another user

        Returns
        -------
        Awaintable[Optional[:class:`Response`]]
            A response, or None if the command was not found

        Raises
        ------
        CommandError
            Thrown on a command error

        """

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
            for i, command in enumerate(split_piped(message.content)):
                message = ProxyMessage(message)
                if input:
                    command = command + " " + input.content
                    message.attachments = input.attachments
                    message.registers = input.registers
                    message.stack = input.stack
                command = interpolate(command, message.registers)
                message.content = command
                message.direct = direct
                input = await self._execute_prefixed(message, context, expect_prefix=False)
                if input:  # if there is no command, it will be None
                    if not input.registers:
                        input.registers = message.registers
                    if not input.stack:
                        input.stack = message.stack
                else:
                    if i != 0:
                        raise CommandError("Command not found: `{}`".format(command))
                    else:
                        break
            return input
        except AuthorizationError as e:
            err = str(e)
            if len(err):
                await message.respond("\N{WARNING SIGN} Auth error: {}".format(err))
            else:
                await message.respond("\N{WARNING SIGN} Whoops -- you can't use this.")
        except ComplexityError as e:
            await message.respond("\N{WARNING SIGN} Your command was too complex to handle. Calm down.")
        except CommandError as e:
            await message.respond("\N{WARNING SIGN} {}".format(str(e)))
        except RateLimitExceeded as e:
            await message.respond("\N{WARNING SIGN} Your command is hitting a rate limit. Try again later.")
        except Exception as e:
            logger.warning("Command raised an exception for '{}'".format(message.content), exc_info=True)
            await message.respond("\N{WARNING SIGN} An unexpected error occurred.")
