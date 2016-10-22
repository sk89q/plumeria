"""Manage the storage and retrieval of per-user preferences."""

from plumeria.command import commands, CommandError
from plumeria.core.user_prefs import prefs_manager
from plumeria.message import Message
from plumeria.message.mappings import build_mapping
from plumeria.perms import direct_only


def find_preference(name):
    try:
        return prefs_manager.get_preference(name)
    except KeyError:
        raise CommandError("No such preference **{}** exists.".format(name))


@commands.create('pref set', 'prefs set', 'pset', cost=4, category='User Preferences')
@direct_only
async def set(message: Message):
    """
    Set a user preference for yourself.

    The values of certain preferences marked private cannot be seen again after it has been set.

    Example::

        /pset ifttt_maker_key N1waEaZ2rUKxbTMTdf
    """
    parts = message.content.split(" ", 1)
    if len(parts) != 2:
        raise CommandError("<name> <value>")

    name, raw_value = parts
    pref = find_preference(name)

    try:
        await prefs_manager.put(pref, message.author, raw_value)
        shown_value = raw_value if not pref.private else "(private)"
        return "Set **{}** to '{}' for yourself.".format(name, shown_value)
    except (NotImplementedError, ValueError) as e:
        raise CommandError("Could not set **{}**: {}".format(name, str(e)))


@commands.create('pref unset', 'prefs unset', 'punset', cost=4, category='User Preferences')
@direct_only
async def unset(message: Message):
    """
    Remove a user preference that you have set.

    Example::

        /punset ifttt_maker_key
    """
    pref = find_preference(message.content.strip())

    try:
        await prefs_manager.remove(pref, message.author)
        return "Removed **{}**.".format(pref.name)
    except KeyError:
        raise CommandError("You haven't set that preference.")
    except NotImplementedError as e:
        raise CommandError("Could not delete **{}**: {}".format(pref.name, str(e)))


@commands.create('pref get', 'prefs get', 'pget', cost=4, category='User Preferences')
async def get(message: Message):
    """
    Get what you have set for a preference.

    The values of private preferences will not be shown.

    Example::

        /pget some_var
    """
    pref = find_preference(message.content.strip())

    try:
        value = await prefs_manager.get(pref, message.author)
        shown_value = value if not pref.private else "(private)"
        return shown_value
    except KeyError:
        raise CommandError("You haven't set that preference.")
    except NotImplementedError as e:
        raise CommandError("Could not get **{}**: {}".format(pref.name, str(e)))


@commands.create('pref list', 'prefs list', 'prefs', cost=4, category='User Preferences')
async def list(message: Message):
    """
    Get a list of preferences that have been set for yourself.

    Private preferences will not be shown with their value.
    """
    try:
        prefs = await prefs_manager.get_all(message.author)
        if len(prefs):
            items = [(pref.name, value if not pref.private else "(private)") for pref, value in prefs]
            return build_mapping(items)
        else:
            raise CommandError("You have not set any preferences.")
    except NotImplementedError as e:
        raise CommandError("Could not get your preferences: {}".format(str(e)))


@commands.create('pref defaults', 'prefs defaults', cost=4, category='User Preferences')
async def list_defaults(message: Message):
    """
    Get a list of preferences that can be set.
    """
    prefs = prefs_manager.get_preferences()
    if len(prefs):
        items = [(pref.name, '{} (value: {})'.format(pref.comment, pref.fallback)) for pref in prefs]
        return build_mapping(items)
    else:
        raise CommandError("No preferences exist to be set.")


def setup():
    commands.add(set)
    commands.add(unset)
    commands.add(get)
    commands.add(list)
    commands.add(list_defaults)
