import random

import dice
from plumeria.command import commands, CommandError
from plumeria.message.lists import parse_list

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


@commands.register('8ball', category='Fun')
async def eight_ball(message):
    """
    Chooses a random response from an 8-ball.

    Example::

        /8ball Will I win a big TV?

    Response::

        Will I win a big TV? Very doubtful
    """
    return "{} **{}**".format(message.content, random.choice(EIGHT_BALL_RESPONSES)).strip()


@commands.register('roll', 'dice', category='Fun')
async def roll(message):
    """
    Rolls dice with support for NdM syntax.

    Example::

        /roll 10d4
        /roll 10d1*4+3d1
        /roll 4+14*3
    """
    try:
        result = dice.roll(message.content)
        if isinstance(result, int):
            return str(result)
        else:
            return " ".join([str(s) for s in result])
    except dice.ParseException as e:
        raise CommandError("Invalid syntax. Use NdM to roll dice.")


@commands.register('choice', 'choose', 'pick', category='Fun')
async def choice(message):
    """
    Chooses a random entry for a list of items separated by
    new lines, semi-colons, commas, or spaces.

    Example::

        /choice takeout, dine-in
        /choice tacos, pho, crepes
    """
    if len(message.content):
        split = parse_list(message.content)
        if len(split) > 1:
            choices = list(map(lambda x: x.strip(), split))
            return random.choice(choices)
        raise CommandError("Provide a comma-separated list of choices")
    else:
        raise CommandError("Provide a comma-separated list of choices")


@commands.register('coin', category='Fun')
async def coin(message):
    """
    Flips a coin.

    Example::

        /coin

    Response::

        heads
    """

    if random.getrandbits(1):
        return "heads"
    else:
        return "tails"
