"""Create and get the results of polls on strawpoll.me."""

import re

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.message.lists import parse_list
from plumeria.util.ratelimit import rate_limit

STRAWPOLL_URL_PATTERN = re.compile("https?://(?:www\\.)?strawpoll\\.me/([0-9]+)", re.IGNORECASE)


def parse_strawpoll_id(s):
    s = s.strip()
    m = STRAWPOLL_URL_PATTERN.search(s)
    if m:
        return int(m.group(1))
    try:
        return int(s)
    except ValueError:
        raise CommandError("No strawpoll.me link or ID found")


@commands.create("strawpoll", category="Search")
@rate_limit()
async def strawpoll(message):
    """
    Create a new strawpoll.me poll.

    Example::

        /strawpoll Who is the prettiest of them all?, Me, You

    """
    choices = parse_list(message.content, allow_spaces=False)
    if len(choices) < 2:
        raise CommandError("Expected a list with two or more times, where the first item is the question")
    if len(choices) > 31:
        raise CommandError("There is a maximum of 30 choices")
    r = await http.post("https://strawpoll.me/api/v2/polls".format(id), data={
        "title": choices[0],
        "options": choices[1:],
    }, headers=(
        ('Content-Type', 'application/json'),
    ), require_success=False)
    data = r.json()
    if r.status_code == 200:
        return "Vote in **{}**: <https://strawpoll.me/{}>".format(choices[0], data['id'])
    else:
        raise CommandError("Strawpolls.me reported an error: {}".format(data['errorMessage']))


@commands.create("strawpoll results", "results", category="Search")
@rate_limit()
async def strawpoll_results(message):
    """
    Get the results of a strawpoll from an ID or a link.

    Example::

        /strawpoll results https://www.strawpoll.me/11094244

    Response::

        21 Yes
        19 Probably

    """
    id = parse_strawpoll_id(message.content)
    r = await http.get("https://www.strawpoll.me/api/v2/polls/{}".format(id), require_success=False)
    data = r.json()
    if r.status_code == 200:
        lines = [data['title']]
        for i, choice in enumerate(data['options']):
            lines.append("{} {}".format(data['votes'][i], choice))
        return "\n".join(lines)
    else:
        raise CommandError("Strawpolls.me reported an error: {}".format(data['errorMessage']))


def setup():
    commands.add(strawpoll)
    commands.add(strawpoll_results)
