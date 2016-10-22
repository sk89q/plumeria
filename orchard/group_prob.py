"""Add a fun 'group 8 ball' command."""

import random

from plumeria.command import commands, channel_only, CommandError
from plumeria.middleware.activity import tracker
from plumeria.transport.status import ONLINE

# maximum number of users if we don't have a list of recent chatters
MAX_USERS = 10


def map_choice(choice):
    return "{clap}**{most}** ({most_pct:.0f}%)".format(
        most=choice[0],
        most_pct=choice[1] * 100,
        clap="\N{CLAPPING HANDS SIGN} " if choice[1] >= 0.9 else "",
    )


@commands.create("group prob", "gp", category="Fun")
@channel_only
async def group_prob(message):
    """
    A fun command that picks random people as "most likely" and "least likely"
    from the channel for a question.

    Example::

        /gp find love in a bathroom
        
    """
    query = message.content.strip()
    if not len(query):
        raise CommandError("A statement or question must be posed!")

    users = await tracker.get_recent_users(message.channel)

    # if we don't have a lot of users, get the member list of the channel
    if len(users) < 2:
        users = []
        for member in message.channel.members:
            # don't include ourselves
            if member == message.channel.transport.user:
                continue
            if member.status == ONLINE:
                users.append(member)
                if len(users) > MAX_USERS:
                    users = []
                    break

    if len(users) < 2:
        raise CommandError("Not enough people have said anything recently to do this command.")

    choices = list(map(lambda user: (user.name, random.random()), users))
    choices.sort(key=lambda c: -c[1])

    return "The most likely to **{question}** is {most} " \
           "and the *least* likely is **{least}** ({least_pct:.0f}%)".format(
        question=query,
        most=", ".join(map(map_choice, choices[:-1][:3])),
        least=choices[-1][0],
        least_pct=choices[-1][1] * 100,
    )


def setup():
    commands.add(group_prob)
