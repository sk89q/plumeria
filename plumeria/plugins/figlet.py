from pyfiglet import Figlet
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit

MAX_LENGTH = 20


@commands.register('figlet', category='Fun')
@rate_limit(burst_size=2)
async def figlet(message):
    """
    Generates ASCII art from text.
    """
    text = message.content.strip()
    if len(text):
        f = Figlet(font='slant')
        return Response("```\n.\n{}```".format(f.renderText(text[:MAX_LENGTH])))
    else:
        raise CommandError("No text provided!")
