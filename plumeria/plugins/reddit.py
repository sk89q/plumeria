import re
import shlex

from plumeria.command import commands, CommandError, ArgumentParser
from plumeria.util import http
from plumeria.util.http import BadStatusCodeError
from plumeria.util.ratelimit import rate_limit


def valid_subreddit_name(s):
    if re.match("^([A-Za-z0-9_]{1,50})$", s):
        return s
    else:
        raise ValueError("Invalid subreddit name")


def format_entry(post):
    data = post['data']
    return "**{title}** <{desc}>".format(
        title=data['title'],
        desc=data['url']
    )


def format_entries(posts, count=5):
    if len(posts):
        posts = map(lambda post: "\u2022 " + format_entry(post), posts[:count])
        return "\n".join(posts)
    else:
        raise CommandError("No entries found")


async def get_subreddit_post(q, top=False, count=5):
    try:
        r = await http.get("https://www.reddit.com/r/{}/{}.json".format(q, "top/" if top else ""), params=([('t', 'all')] if top else []))
        return format_entries(r.json()['data']['children'], count)
    except BadStatusCodeError as e:
        raise CommandError("Got {} error code".format(e.http_code))


@commands.register("reddit", "subreddit" "r/", category="Reddit")
@rate_limit()
async def subreddit(message):
    """
    Get the hottest posts from a subreddit.

    """
    parser = ArgumentParser()
    parser.add_argument("subreddit", type=valid_subreddit_name)
    parser.add_argument("count", type=int, nargs='?', default=5, choices=range(1, 10))
    args = parser.parse_args(shlex.split(message.content))
    return "/r/{}\n{}".format(args.subreddit, await get_subreddit_post(args.subreddit, count=args.count))


@commands.register("reddittop", "topreddit", "subreddittop", "r/top", "r/top/", category="Reddit")
@rate_limit()
async def subreddit_top(message):
    """
    Get the top post from a subreddit.

    """
    parser = ArgumentParser()
    parser.add_argument("subreddit", type=valid_subreddit_name)
    parser.add_argument("count", type=int, nargs='?', default=5, choices=range(1, 10))
    args = parser.parse_args(shlex.split(message.content))
    return "/r/top/{}\n{}".format(args.subreddit, await get_subreddit_post(args.subreddit, count=args.count, top=True))


@commands.register("redditsearch", "rs", category="Reddit")
@rate_limit()
async def search_reddit(message):
    """
    Search Reddit for a post.

    """
    q = message.content
    try:
        r = await http.get("https://www.reddit.com/r/videos/search.json", params=[
            ('q', q),
            ('sort', 'relevance'),
            ('t', 'all')
        ])
        return "Search results:\n" + format_entries(r.json()['data']['children'], 5)
    except BadStatusCodeError as e:
        raise CommandError("Got {} error code".format(e.http_code))
