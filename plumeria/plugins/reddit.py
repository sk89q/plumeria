import re

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.http import BadStatusCodeError
from plumeria.util.ratelimit import rate_limit


def format_first_entry(listing):
    posts = listing['data']['children']
    if len(posts):
        post = posts[0]['data']
        return "{title} - {desc}".format(
            title=post['title'],
            desc=post['url']
        )
    else:
        raise CommandError("No entries found")


async def get_subreddit_post(message, top=False):
    q = message.content.strip()
    if not q:
        raise CommandError("Subreddit name required!")
    elif not re.match("^([A-Za-z0-9_]+)$", q):
        raise CommandError("Invalid subreddit name!")
    try:
        r = await http.get("https://www.reddit.com/r/{}/{}.json".format(q, "top/" if top else ""), params=[])
        return format_first_entry(r.json())
    except BadStatusCodeError as e:
        raise CommandError("Got {} error code".format(e.http_code))


@commands.register("subreddit", "r/", category="Reddit")
@rate_limit()
async def subreddit(message, top=False):
    """
    Get the hottest post from a subreddit.

    """
    return await get_subreddit_post(message)


@commands.register("subreddittop", "r/top", "r/top/", category="Reddit")
@rate_limit()
async def subreddit_top(message):
    """
    Get the top post from a subreddit.

    """
    return await get_subreddit_post(message, top=True)


@commands.register("redditsearch", "rs", category="Reddit")
@rate_limit()
async def search_reddit(message, top=False):
    """
    Search Reddit for a post.

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    try:
        r = await http.get("https://www.reddit.com/r/videos/search.json", params=[
            ('q', q),
            ('sort', 'relevance'),
            ('t', 'all')
        ])
        return format_first_entry(r.json())
    except BadStatusCodeError as e:
        raise CommandError("Got {} error code".format(e.http_code))
