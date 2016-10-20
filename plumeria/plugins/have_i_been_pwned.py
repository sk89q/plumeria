import plumeria.util.http as http
from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.message.mappings import build_mapping
from plumeria.util.collections import SafeStructure
from plumeria.util.ratelimit import rate_limit


@commands.register("haveibeenpwned", "pwned", category="Search", params=[Text('query')])
@rate_limit(burst_size=4)
async def have_i_been_pwned(message, query):
    """
    Checks where an account (specified by account name or email address) exists
    on sites that have experienced data breaches.

    Example::

        pwned email@example.com

    """
    r = await http.get("https://haveibeenpwned.com/api/v2/breachedaccount/" + query, headers=[
        ('User-Agent', 'Plumeria chat bot (+https://gitlab.com/sk89q/Plumeria)')
    ])

    if not len(r.text().strip()):
        raise CommandError("Account not found! (That's good.)")

    results = SafeStructure(r.json())

    return build_mapping(
        [(e.Title, "{} ({} breached) ({})".format(e.BreachDate, e.PwnCount, ", ".join(e.DataClasses))) for e in
         results])
