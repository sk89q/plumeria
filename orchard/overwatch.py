"""Get stats for Overwatch."""

from plumeria.command import commands, CommandError
from plumeria.command.parse import Word
from plumeria.message.lists import build_list
from plumeria.util import http
from plumeria.util.http import BadStatusCodeError
from plumeria.util.ratelimit import rate_limit

GENERAL_STATS = (
    ('Played', 'time_played', '{:.0f}'),
    ('K/D', 'kpd', '{:.2f}'),
    ('Dmg/t', 'all_damage_done_avg_per_10_min', '{:.0f}'),
    ('Best Streak', 'kill_streak_best', '{:.0f}'),
    ('Obj Time/g', 'objective_time_most_in_game', '{:.5f}'),
    ('Most Dmg/g', 'all_damage_done_most_in_game', '{:.0f}'),
    ('Most Heal/g', 'healing_done_most_in_game', '{:.0f}'),
    ('Medals', 'medals', '{:.0f}'),
    ('Gold Med', 'medals_gold', '{:.0f}'),
    ('Won', 'games_won', '{:.0f}'),
)


def generate_stats_from_keys(data, stats):
    entries = []
    for label, key, format in stats:
        if key in data:
            entries.append(('{}: **' + format + '**').format(label, float(data[key])))
    return ' | '.join(entries)


@commands.create('overwatch', 'ow', cost=2, category='Games', params=[Word('battletag'), Word('region', fallback=None)])
@rate_limit()
async def overwatch(message, battletag, region=None):
    """
    Get someone's Overwatch stats.

    The name is case-sensitive.

    Example::

        /overwatch booo#0000

    """
    try:
        r = await http.get("https://owapi.net/api/v3/u/{name}/blob".format(name=battletag.replace("#", "-")))
        data = r.json()
    except BadStatusCodeError as e:
        if e.http_code == 404:
            raise CommandError("Battletag '{}' not found. The name is CASE-SENSITIVE.".format(battletag))
        raise

    regions = []
    for key, value in data.items():
        if key[0] != "_" and value:
            regions.append(key)

    if not len(regions):
        raise CommandError("Battle tag found but there are no stats for '{}'.".format(battletag))
    if not region and len(regions) > 1:
        raise CommandError("Please specify a region (one of {}) for '{}'.".format(', '.join(regions), battletag))
    if region and region.lower() not in regions:
        raise CommandError("Please specify a region in one of {} for '{}'.".format(', '.join(regions), battletag))

    if not region:
        region = regions[0]
    stats = data[region]

    lines = []
    for type, s in stats['stats'].items():
        lines.append(
            "**{}**: {}".format(type.capitalize(), generate_stats_from_keys(s['game_stats'], GENERAL_STATS)))
    return build_list(lines)


def setup():
    commands.add(overwatch)
