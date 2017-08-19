from functools import wraps

from plumeria.command import CommandError


async def get_voice_client(member, move_to=False, any_channel=False):
    user_voice_channel = member.voice.voice_channel
    if user_voice_channel is None:
        raise CommandError("You are not currently in a voice channel.")
    voice_client = member.transport.voice_client_in(member.server)
    if voice_client is None:
        return await member.transport.join_voice_channel(user_voice_channel)
    elif voice_client.channel != user_voice_channel:
        if move_to:
            await voice_client.move_to(user_voice_channel)
            return user_voice_channel
        elif any_channel:
            return voice_client
        else:
            raise CommandError("The bot is busy in another voice channel.")
    else:
        return voice_client


def voice_with_bot_only(f):
    """Make sure that the command is being run by a user in the same voice channel as the bot."""

    @wraps(f)
    async def wrapper(message, *args, **kwargs):
        await get_voice_client(message.author)
        return await f(message, *args, **kwargs)

    wrapper.voice_with_bot_only = True
    return wrapper
