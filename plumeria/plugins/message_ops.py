from plumeria.command import CommandError, commands
from plumeria.message import Response, Message, ProxyMessage
from plumeria.message.lists import parse_list


@commands.register('push', 'psh', cost=0.05, category="Operations")
async def push(message):
    """
    Pushes a message to the stack.

    Example::

        /push
    """
    message.stack.append(message)


@commands.register('pop', cost=0.05, category="Operations")
async def pop(message):
    """
    Pops a message from the stack.

    Example::

        /push
    """
    try:
        ret = message.stack.pop()
        return Response(ret.content, attachments=ret.attachments[:])
    except IndexError:
        raise CommandError("stack is empty")


@commands.register('put', 'store', 'stor', cost=0.05, category="Operations")
async def put(message):
    """
    Puts a message into a given register.

    Example::

        /put eax
    """
    parts = message.content.split(" ", 1)
    key = parts[0].strip()
    message_copy = ProxyMessage(message)
    message_copy.content = parts[1]
    message.registers[key] = message_copy
    return Response("", registers=message.registers)


@commands.register('get', cost=0.05, category="Operations")
async def get(message):
    """
    Reads a message from a given register.

    Example::

        /get eax
    """
    parts = message.content.split(" ", 2)
    key = parts[0].strip()
    try:
        ret = message.registers[key]
        return Response(ret.content, attachments=ret.attachments[:])
    except KeyError:
        raise CommandError("no key '{}' in registers".format(key))


@commands.register('argparse', cost=0.05, category="Operations")
async def argparse(message):
    """
    Parse arguments from input and save them into registers. To use the command,
    the list of parameter names (register names) must be provided, separated
    by spaces, and then this list must be ended with a standalone @ symbol.
    After the @ symbol must be the arguments that will be parsed.
    If there are not enough arguments, an error will be raised.

    Example::

        /echo Bobby 63 | argparse name age @
    """
    parts = message.content.split(" ")
    params = []
    input = None
    for i, part in enumerate(parts):
        if part == "@":
            if len(parts) > i + 1:
                input = " ".join(parts[i + 1:])
            else:
                input = ""
            break
        else:
            params.append(part)
    args = parse_list(input, allow_spaces=True)
    if len(args) < len(params):
        raise CommandError("not enough arguments (expected {})".format(", ".join(params)))
    else:
        for i, key in enumerate(params):
            new_message = ProxyMessage(message)
            new_message.content = args[i]
            new_message.attachments = []
            message.registers[key] = new_message
