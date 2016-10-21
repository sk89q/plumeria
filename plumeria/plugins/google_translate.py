"""Translate some text with Google Translate."""

import json
import re

import pycountry
from titlecase import titlecase

from plumeria.command import commands, CommandError
from plumeria.message import Message
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


def find_language(code):
    try:
        return pycountry.languages.get(iso639_1_code=code)
    except:
        pass
    try:
        return pycountry.languages.get(name=titlecase(code))
    except:
        pass
    raise CommandError("Unknown language code: {}".format(code))


@commands.create("translate", category="Search")
@rate_limit()
async def translate(message: Message):
    """
    Translates text to another language.

    Example::

        /translate en fr hello
    """
    parts = message.content.strip().split(" ", maxsplit=2)
    if len(parts) < 3:
        raise CommandError("At least 3 parameters are required: from language, to language, and the text")

    from_lang, to_lang, text = parts
    from_lang = find_language(from_lang)
    to_lang = find_language(to_lang)

    if from_lang == to_lang:
        raise CommandError("The 'from language' can't be the same as the 'to language'.")

    r = await http.get("https://translate.googleapis.com/translate_a/single", params={
        "client": "gtx",
        "sl": from_lang.iso639_1_code,
        "tl": to_lang.iso639_1_code,
        "dt": "t",
        "q": text,
    }, headers={
        ('User-Agent',
         'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36')
    })

    # this isn't very right
    raw_data = re.sub(",,+", ",", r.text())
    raw_data = raw_data.replace("[,", "[")
    raw_data = raw_data.replace(",]", "]")

    data = json.loads(raw_data)
    if isinstance(data[0], list):
        translations = data[0]
        return "".join([e[0].replace("\\n", "\n") for e in translations])
    else:
        raise CommandError("Translation not available.")


def setup():
    commands.add(translate)
