import uuid

from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.command import string_filter


@commands.register('uuid', category='String')
async def random_uuid(message):
    """
    Generates a random UUID.
    """
    return Response(str(uuid.uuid4()))


@commands.register('dashuuid', category='String')
@string_filter
def dash_uuid(text):
    """
    Formats a UUID with dashes.
    """
    try:
        return str(uuid.UUID(text))
    except ValueError as e:
        raise CommandError("Invalid UUID provided.")


@commands.register('hexuuid', category='String')
@string_filter
def hex_uuid(text):
    """
    Formats a UUID without dashes.
    """
    try:
        return uuid.UUID(text).hex
    except ValueError as e:
        raise CommandError("Invalid UUID provided.")
