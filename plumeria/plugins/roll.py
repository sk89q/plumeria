import random

import dice
from plumeria.command import commands, CommandError


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
        split = message.content.split(",")
        if len(split) > 1:
            choices = list(map(lambda x: x.strip(), split))
            return random.choice(choices)
        raise CommandError("Provide a comma-separated list of choices")
    else:
        raise CommandError("Provide a comma-separated list of choices")
