"""Commands to manipulate text."""

import re
import urllib.parse

import codecs
import hashlib
from plumeria.command import commands, CommandError
from plumeria.message.lists import parse_list
from plumeria.message.mappings import parse_mapping
from plumeria.util.ratelimit import rate_limit
from plumeria.util.command import string_filter

MD_BOLD_RE = re.compile("\\*\\*(.+?)\\*\\*")
LINK_PATTERN = re.compile("<?((https?)://[^\s/$.?#<>].[^\s<>]*)>?", re.I)


@commands.create('upper', category='String')
@string_filter
def upper(text):
    """
    Uppercases given text.
    """
    return text.upper()


@commands.create('lower', category='String')
@string_filter
def lower(text):
    """
    Lowercases given text.
    """
    return text.lower()


@commands.create('rot13', category='String')
@string_filter
def rot13(text):
    """
    ROT13 transforms given text.
    """
    return codecs.encode(text, "rot_13")


@commands.create('idna', category='String')
@string_filter
def idna(text):
    """
    IDNA transforms given text.
    """
    return codecs.encode(text, "idna").decode('utf-8')


@commands.create('punycode', category='String')
@string_filter
def punycode(text):
    """
    Punycode transforms given text.
    """
    return codecs.encode(text, "punycode").decode('utf-8')


@commands.create('base64', 'base64enc', category='String')
@rate_limit()
@string_filter
def base64(text):
    """
    Base64 encodes given text.
    """
    return codecs.encode(text.encode('utf-8'), "base64").decode('ascii')


@commands.create('base64dec', category='String')
@rate_limit()
@string_filter
def base64_decode(text):
    """
    Base64 decodes given text.
    """
    return codecs.decode(text.encode('utf-8'), "base64").decode('utf-8', 'ignore')


@commands.create('md5', category='String')
@rate_limit()
@string_filter
def md5(text):
    """
    MD5 hashes given text.
    """
    return hashlib.md5(text)


@commands.create('sha1', category='String')
@rate_limit()
@string_filter
def sha1(text):
    """
    SHA1 hashes given text.
    """
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


@commands.create('sha224', category='String')
@rate_limit(burst_size=3)
@string_filter
def sha224(text):
    """
    SHA224 hashes given text.
    """
    return hashlib.sha224(text.encode('utf-8')).hexdigest()


@commands.create('sha256', category='String')
@rate_limit(burst_size=3)
@string_filter
def sha256(text):
    """
    SHA256 hashes given text.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@commands.create('urlescape', category='String')
@string_filter
def urlescape(text):
    """
    Percent-escapes the given text.

    Spaces are replaced with a plus (+).
    """
    return urllib.parse.quote_plus(text)


@commands.create('unurlescape', category='String')
@string_filter
def unurlescape(text):
    """
    Percent-unescapes the given text.

    Pluses (+) are replaced with a space.
    """
    return urllib.parse.unquote_plus(text)


@commands.create('length', category='String')
@string_filter
def length(text):
    """
    Returns the length of the given string.
    """
    return str(len(text))


@commands.create('findurl', category='String')
@string_filter
def find_url(text):
    """
    Returns the first URL in the string.
    """
    m = LINK_PATTERN.search(text)
    if m:
        return m.group(1)
    else:
        raise CommandError("No URL found in string")


@commands.create('stripurl', category='String')
@string_filter
def strip_html(text):
    """
    Strip URLs from a string.
    """
    return LINK_PATTERN.sub('', text)


@commands.create('strip', category='String')
@string_filter
def strip(text):
    """
    Strings a string of surrounding whitespace.
    """
    return text.strip()


@commands.create('extract', category='String')
@string_filter
def extract(text):
    """
    Tries to extract the first result from a string.
    """
    item = parse_list(text, allow_spaces=True)[0].strip()
    m = MD_BOLD_RE.search(item)
    if m:
        return m.group(1)
    else:
        return item


@commands.create('first', category='String')
@string_filter
def first(text):
    """
    Gets the first value of a list of items.
    """
    return parse_list(text, allow_spaces=True)[0]


@commands.create('end', category='String')
@string_filter
def last(text):
    """
    Gets the last value of a list of items.
    """
    return parse_list(text, allow_spaces=True)[-1]


@commands.create('key', category='String')
async def map_get(message):
    """
    Fetches a key from a "mapping." Some commands return a list of key: value lines.

    Example::

        /key display_name
        ID: 32234
        Display Name: Bob

    Response::

        Bob

    """
    parts = message.content.strip().split(" ", 1)
    if len(parts) == 1:
        raise CommandError("Need a key and then the mapping")
    key = parts[0].strip()
    test_key = key.lower()
    text = parts[1]
    for k, v in parse_mapping(text):
        if k.replace(" ", "_").lower() == test_key:
            return v
    raise CommandError("Could not find '{}' in mapping".format(key))


def setup():
    commands.add(upper)
    commands.add(lower)
    commands.add(rot13)
    commands.add(idna)
    commands.add(punycode)
    commands.add(base64)
    commands.add(base64_decode)
    commands.add(md5)
    commands.add(sha1)
    commands.add(sha224)
    commands.add(sha256)
    commands.add(urlescape)
    commands.add(unurlescape)
    commands.add(length)
    commands.add(find_url)
    commands.add(strip_html)
    commands.add(strip)
    commands.add(extract)
    commands.add(first)
    commands.add(last)
    commands.add(map_get)
