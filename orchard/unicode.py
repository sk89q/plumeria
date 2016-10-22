"""Utility commands to work Unicode data."""

import unicodedata

from plumeria.command import commands
from plumeria.util.command import string_filter


@commands.create('unicode escape', 'unicodeescape', category='Development')
@string_filter
def unicode_escape(text):
    """
    Escapes unicode characters in the given string into a format compatible
    with Python, C#, C++11, and many other programming languages. BMP characters
    are escaped as ``\\u####`` and non-BMP characters are escaped as
    ``\\U########``. The former syntax is compatible with Java and other
    languages, but the latter syntax is not.

    Example::

        .unicodeescape \U0001f50a \u266b Yeah, you take these dreams and throw them out the window \u266b

    Response::

        \\U0001f50a \\u266b Yeah, you take these dreams and throw them out the window \\u266b

    """
    return text.encode("unicode_escape").decode("utf-8")


@commands.create('unicode name', 'unicodename', category='Development')
@string_filter
def unicode_name(text):
    """
    Finds the Unicode names for the given characters, up to 10 characters.

    """
    return "\n".join(s + " **" + unicodedata.name(s, "?") + "**" for s in text[:10])



@commands.create('unicode code', 'unicodecode', category='Development')
@string_filter
def unicode_code(text):
    """
    Finds the Unicode code points for the given characters, up to 10 characters.

    """
    return "\n".join("{} **{}**".format(s, ord(s)) for s in text[:10])


def setup():
    commands.add(unicode_escape)
    commands.add(unicode_name)
    commands.add(unicode_code)
