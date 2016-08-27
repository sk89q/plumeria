import random

import dice
from plumeria.command import commands, CommandError
from plumeria.util.message import split_array

EIGHT_BALL_RESPONSES = (
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes, definitely",
    "You may rely on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful",
)


@commands.register('8ball', category='Utility')
async def eight_ball(message):
    """
    Chooses a random response from an 8-ball.
    """
    return "{} **{}**".format(message.content, random.choice(EIGHT_BALL_RESPONSES)).strip()


@commands.register('roll', category='Utility')
async def roll(message):
    """
    Rolls dice with support for NdM syntax.
    """
    try:
        result = dice.roll(message.content)
        if isinstance(result, int):
            return str(result)
        else:
            return " ".join([str(s) for s in result])
    except dice.ParseException as e:
        raise CommandError("Invalid syntax. Use NdM to roll dice.")


@commands.register('choice', 'choose', 'pick', category='Utility')
async def choice(message):
    """
    Chooses a random entry for a list of comma-separated choices.:
    """
    if len(message.content):
        split = split_array(message.content)
        if len(split) > 1:
            choices = list(map(lambda x: x.strip(), split))
            return random.choice(choices)
        raise CommandError("Provide a comma-separated list of choices")
    else:
        raise CommandError("Provide a comma-separated list of choices")
