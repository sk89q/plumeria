import urllib.parse

import codecs
import hashlib
from plumeria.command import commands
from plumeria.util.ratelimit import rate_limit
from plumeria.util.command import string_filter


@commands.register('upper', category='String')
@string_filter
def upper(text):
    """
    Uppercases given text.
    """
    return text.upper()


@commands.register('lower', category='String')
@string_filter
def lower(text):
    """
    Lowercases given text.
    """
    return text.lower()


@commands.register('rot13', category='String')
@string_filter
def rot13(text):
    """
    ROT13 transforms given text.
    """
    return codecs.encode(text, "rot_13")


@commands.register('idna', category='String')
@string_filter
def idna(text):
    """
    IDNA transforms given text.
    """
    return codecs.encode(text, "idna").decode('utf-8')


@commands.register('punycode', category='String')
@string_filter
def punycode(text):
    """
    Punycode transforms given text.
    """
    return codecs.encode(text, "punycode").decode('utf-8')


@commands.register('base64', 'base64enc', category='String')
@rate_limit()
@string_filter
def base64(text):
    """
    Base64 encodes given text.
    """
    return codecs.encode(text.encode('utf-8'), "base64").decode('ascii')


@commands.register('base64dec', category='String')
@rate_limit()
@string_filter
def base64_decode(text):
    """
    Base64 decodes given text.
    """
    return codecs.decode(text.encode('utf-8'), "base64").decode('utf-8', 'ignore')


@commands.register('md5', category='String')
@rate_limit()
@string_filter
def md5(text):
    """
    MD5 hashes given text.
    """
    return hashlib.md5(text)


@commands.register('sha1', category='String')
@rate_limit()
@string_filter
def sha1(text):
    """
    SHA1 hashes given text.
    """
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


@commands.register('sha224', category='String')
@rate_limit(burst_size=3)
@string_filter
def sha224(text):
    """
    SHA224 hashes given text.
    """
    return hashlib.sha224(text.encode('utf-8')).hexdigest()


@commands.register('sha256', category='String')
@rate_limit(burst_size=3)
@string_filter
def sha256(text):
    """
    SHA256 hashes given text.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@commands.register('urlescape', category='String')
@string_filter
def urlescape(text):
    """
    Percent-escapes the given text.

    Spaces are replaced with a plus (+).
    """
    return urllib.parse.quote_plus(text)


@commands.register('unurlescape', category='String')
@string_filter
def unurlescape(text):
    """
    Percent-unescapes the given text.

    Pluses (+) are replaced with a space.
    """
    return urllib.parse.unquote_plus(text)


@commands.register('length', category='String')
@string_filter
def length(text):
    """
    Returns the length of the given string.
    """
    return str(len(text))
