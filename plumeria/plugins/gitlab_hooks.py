import json
import logging
import re
import shlex

import rethinkdb as r

from plumeria.command import commands, channel_only, CommandError, ArgumentParser
from plumeria.event import bus
from plumeria.perms import server_admins_only
from plumeria.rethinkdb import migrations, pool
from plumeria.transport import transports
from plumeria.webserver import app

WEB_HOOK_URL = "/gitlab-webhooks/hook/"
TOKENS_TABLE = "gitlabhooks_tokens"
SUBSCRIPTIONS_TABLE = "gitlabhooks_subscriptions"

logger = logging.getLogger(__name__)


def valid_project_path(s):
    if re.match("^[A-Za-z0-9\\-_\\.,]{1,100}/[A-Za-z0-9\\-_\\.,]{1,100}$", s):
        return s
    raise ValueError("Invalid project! Must match regex `^[A-Za-z0-9\\-_]{1,100}/[A-Za-z0-9\\-_]{1,100}$`")


@bus.event('preinit')
async def preinit():
    async def initial(conn):
        await r.table_create(TOKENS_TABLE).run(conn)
        await r.table(TOKENS_TABLE).index_create("server_id", r.row["server_id"]).run(conn)
        await r.table_create(SUBSCRIPTIONS_TABLE).run(conn)
        await r.table(SUBSCRIPTIONS_TABLE).index_create("server_id_channel_id",
                                                        [r.row["server_id"], r.row["channel_id"]]).run(conn)
        await r.table(SUBSCRIPTIONS_TABLE).index_create("server_id_channel_id_project_path",
                                                        [r.row["server_id"], r.row["channel_id"],
                                                         r.row['project_path']]).run(conn)

    await migrations.migrate("gitlab_hooks",
                             (("initial", initial),))


@commands.register('gitlab url', category='GitLab')
@channel_only
@server_admins_only
async def url(message):
    """
    Get the webhook URL to use.
    """
    return "Send webhook POSTs to `{}{}`".format(await app.get_base_url(), WEB_HOOK_URL)


@commands.register('gitlab addtoken', category='GitLab')
@channel_only
@server_admins_only
async def add_token(message):
    """
    Add a token that must be present for GitLab hooks to work.
    """
    token = message.content.strip()
    if not re.match("^([^ ]+){1,50}$", token):
        raise CommandError("Tokens should mach the regex `^([^ ]+){1,50}$`.")
    async with pool.acquire() as conn:
        cursor = await r.table(TOKENS_TABLE).filter({"server_id": message.channel.server.id,
                                                     "token": token}).run(conn)
        if not await cursor.fetch_next():
            await r.table(TOKENS_TABLE).insert({
                "server_id": message.channel.server.id,
                "token": token}).run(conn)
            return "\u2705 Token '{}' added. Send webhook POSTs to `{}{}`" \
                .format(token, await app.get_base_url(), WEB_HOOK_URL)
        else:
            raise CommandError("Token '{}' was already added.".format(token))


@commands.register('gitlab removetoken', 'gitlab deletetoken', category='GitLab')
@channel_only
@server_admins_only
async def remove_token(message):
    """
    Remove a token that was previously added.
    """
    token = message.content.strip()
    if not re.match("^([^ ]+){1,50}$", token):
        raise CommandError("Tokens should mach the regex `^([^ ]+){1,50}$`.")
    async with pool.acquire() as conn:
        ret = await r.table(TOKENS_TABLE).filter({
            "server_id": message.channel.server.id,
            "token": token}).delete().run(conn)
        if ret['deleted'] > 0:
            return "\u2705 Token '{}' deleted.".format(token)
        else:
            raise CommandError("The token '{}' wasn't added yet.".format(token))


@commands.register('gitlab tokens', category='GitLab')
@channel_only
@server_admins_only
async def subscriptions(message):
    """
    Get a list of active webhook tokens for this server.
    """
    async with pool.acquire() as conn:
        cursor = await r.table(TOKENS_TABLE) \
            .filter({"server_id": message.channel.server.id}) \
            .run(conn)
        tokens = []
        while await cursor.fetch_next():
            tokens.append((await cursor.next())['token'])
        if len(tokens):
            return ", ".join(map(lambda x: "`{}`".format(x), tokens))
        else:
            raise CommandError("No tokens added yet!")


@commands.register('gitlab subscribe', 'gitlab sub', category='GitLab')
@channel_only
@server_admins_only
async def subscribe(message):
    """
    Subscribe to events for a repository on GitLab.
    """
    parser = ArgumentParser()
    parser.add_argument("project_path", type=valid_project_path)
    parser.add_argument("events", nargs="*")
    args = parser.parse_args(shlex.split(message.content))
    events = args.events if len(args.events) else ('push',)

    async with pool.acquire() as conn:
        await r.table(SUBSCRIPTIONS_TABLE) \
            .filter({"server_id": message.channel.server.id,
                     "channel_id": message.channel.id,
                     "project_path": args.project_path}) \
            .delete() \
            .run(conn)
        await r.table(SUBSCRIPTIONS_TABLE).insert({"server_id": message.channel.server.id,
                                                   "channel_id": message.channel.id,
                                                   "project_path": args.project_path,
                                                   "events": events}).run(conn)

    return "\u2705 Subscribed to **{project_path}** in **#{channel}** for events: {events}" \
        .format(project_path=args.project_path,
                channel=message.channel.name,
                events=", ".join(events))


@commands.register('gitlab unsubscribe', 'gitlab unsub', category='GitLab')
@channel_only
@server_admins_only
async def unsubscribe(message):
    """
    Unsubscribe from events for a repository.
    """
    parser = ArgumentParser()
    parser.add_argument("project_path", type=valid_project_path)
    args = parser.parse_args(shlex.split(message.content))

    async with pool.acquire() as conn:
        ret = await r.table(SUBSCRIPTIONS_TABLE) \
            .filter({"server_id": message.channel.server.id,
                     "channel_id": message.channel.id,
                     "project_path": args.project_path}) \
            .delete() \
            .run(conn)
        if ret['deleted'] == 1:
            return "Unsubscribed from '{}'.".format(args.project_path)
        else:
            raise CommandError("This channel wasn't subscribed to events from that repository.")


@commands.register('gitlab subscriptions', 'gitlab subs', category='GitLab')
@channel_only
@server_admins_only
async def subscriptions(message):
    """
    Get a list of active subscriptions for this channel.
    """
    async with pool.acquire() as conn:
        cursor = await r.table(SUBSCRIPTIONS_TABLE) \
            .filter({"server_id": message.channel.server.id,
                     "channel_id": message.channel.id}) \
            .run(conn)
        projects = []
        while await cursor.fetch_next():
            projects.append((await cursor.next())['project_path'])
        if len(projects):
            return ", ".join(map(lambda x: "`{}`".format(x), projects))
        else:
            raise CommandError("This channel is not subscribed to any notifications from any GitLab repositories.")


def format_message(payload):
    if payload['event_name'] == 'push':
        if payload['before'] == "0000000000000000000000000000000000000000":
            return "\U0001F539 [**{project}**] New branch **{branch}** was pushed by {author}".format(
                project=payload['project']['path_with_namespace'],
                branch=re.sub("^refs/heads/", "", payload['ref']),
                author=payload['user_name'])
        elif payload['after'] == "0000000000000000000000000000000000000000":
            return "\U0001F539 [**{project}**] Branch **{branch}** deleted by {author}".format(
                project=payload['project']['path_with_namespace'],
                branch=re.sub("^refs/heads/", "", payload['ref']),
                author=payload['user_name'])
        else:
            commit_count = len(payload['commits'])
            commits = "\n".join(map(lambda commit: "\u2022 {}: {}"
                                    .format(commit['id'][:8], commit['message'].splitlines()[0]),
                                    payload['commits'][:5]))
            return "\U0001F539 [**{project}** on **{branch}**] {count} commit{s} by {author}:\n{commits}{more}".format(
                count=commit_count,
                s="s" if commit_count != 1 else "",
                project=payload['project']['path_with_namespace'],
                branch=re.sub("^refs/heads/", "", payload['ref']),
                author=payload['user_name'],
                hash=payload['after'][:8],
                commits=commits,
                more="\n+{} more".format(commit_count - 5) if commit_count > 5 else "",
                url=payload['repository']['homepage'])


@app.route(WEB_HOOK_URL, methods=['POST'])
async def handle(request):
    token = request.headers.get("X-Gitlab-Token", "")
    token_override = request.GET.get("__token", "")

    if len(token_override):
        token = token_override

    if not len(token):
        logger.debug("Received GitLab hook from {} with no token".format(request.transport.get_extra_info('peername')))
        return "no token"
    else:
        logger.debug(
            "Received GitLab hook from {} with token '{}'".format(request.transport.get_extra_info('peername'), token))

    data = await request.text()
    payload = json.loads(data)
    event = payload['event_name']
    project_path = payload['project']['path_with_namespace']

    async with pool.acquire() as conn:
        cursor = await r.table(TOKENS_TABLE) \
            .filter({"token": token}) \
            .inner_join(r.table(SUBSCRIPTIONS_TABLE),
                        lambda token_row, sub_row: token_row['server_id'] == sub_row['server_id']) \
            .run(conn)

        while await cursor.fetch_next():
            row = await cursor.next()
            if event not in row['right']['events']:
                continue
            if project_path != row['right']['project_path']:
                continue

            for transport in transports.transports.values():
                for server in transport.servers:
                    if server.id == row['left']['server_id']:
                        for channel in server.channels:
                            if channel.id == row['right']['channel_id']:
                                await channel.send_message(format_message(payload))

    return "OK"
