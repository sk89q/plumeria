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
