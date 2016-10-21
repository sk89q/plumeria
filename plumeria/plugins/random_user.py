"""Generate random, fake user information using randomuser.me."""

from plumeria.command import commands
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


@commands.create("random user", category="Development")
@rate_limit()
async def random_user(message):
    """
    Get details for a random user generated from randomuser.me.

    Example::

        /random user

    Response::

        Perry Sullivan
        8776 Nowlin Rd, Pomona, Hawaii 38369
        DOB: 1968-06-05 06:03:33

    """
    r = await http.get("https://randomuser.me/api/")
    user = r.json()['results'][0]
    return "{first} {last}\n{street}, {city}, {state} {postcode}\nDOB: {dob}".format(
        first=user['name']['first'].title(),
        last=user['name']['last'].title(),
        street=user['location']['street'].title(),
        city=user['location']['city'].title(),
        postcode=user['location']['postcode'],
        state=user['location']['state'].title(),
        dob=user['dob'].title(),
    )


def setup():
    commands.add(random_user)
