from plumeria.command import commands
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


@commands.register("random user", category="Development")
@rate_limit()
async def random_user(message):
    """
    Get details for a random user generated from randomuser.me.

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
