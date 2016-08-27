import re
import shlex

from plumeria.command import commands, CommandError, ArgumentParser
from plumeria.util import http
from plumeria.util.http import BadStatusCodeError
from plumeria.util.ratelimit import rate_limit

REDDIT_TRIM_PATTERN = re.compile("^/?(r/[^/]+/comments/[^/]+/).*")


def valid_subreddit_name(s):
    if re.match("^([A-Za-z0-9_]{1,50})$", s):
        return s
    else:
        raise ValueError("Invalid subreddit name")


def trim_reddit_link(s):
    return REDDIT_TRIM_PATTERN.sub("\\1", s)


def format_entry(post):
    data = post['data']
    return "**{title}** <https://reddit.com/{desc}>".format(
        title=data['title'],
        desc=trim_reddit_link(data['permalink'])
    )


def format_entries(posts, count=5):
    if len(posts):
        posts = map(lambda post: "\u2022 " + format_entry(post), posts[:count])
        return "\n".join(posts)
    else:
        raise CommandError("No entries found")


async def get_subreddit_post(q, top=False, count=5):
    try:
        r = await http.get("https://www.reddit.com/r/{}/{}.json".format(q, "top/" if top else ""),
                           params=([('t', 'all')] if top else []))
        return format_entries(r.json()['data']['children'], count)
    except BadStatusCodeError as e:
        raise CommandError("Got {} error code".format(e.http_code))


@commands.register("reddit", "subreddit" "r/", category="Reddit")
@rate_limit()
async def subreddit(message):
    """
    Get the hottest posts from a subreddit, with an optional parameter to
    specify the number of posts to get.

    Example::

        /reddit hiphopheads
        /reddit hiphopheads 10

    Response::

        \u2022 i'm slug from atmosphere. aMA https:/[...]
        \u2022 Frank Ocean gets first #1 album with[...]
        \u2022 [FRESH] Isaiah Rashad - Park https://r[...]
        \u2022 [FRESH VIDEO] Capital STEEZ - Herban [...]
        \u2022 Frank Ocean - Blonde, over 750k people [...]

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
    Get the all-time top posts from a subreddit, with an optional parameter to
    specify the number of posts to get

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
    Search Reddit for posts.

    Example::

        .redditsearch the wonder years

    Response::

        \u2022 I am producer and actor Jason H[...]
        \u2022 The Wonder Years - No Closer To [...]
        \u2022 I’m Daniel Stern. You might know [...]
        \u2022 Winnie Cooper from The Wonder Year[...]
        \u2022 The Wonder Years Fall Tour https:/[...]

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
