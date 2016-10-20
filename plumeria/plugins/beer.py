import plumeria.util.http as http
from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.message.mappings import build_mapping
from plumeria.util.collections import SafeStructure
from plumeria.util.ratelimit import rate_limit

api_key = config.create("brewerydb", "key",
                        fallback="unset",
                        comment="An API key from brewerydb.com")


@commands.register("beer", category="Search", params=[Text('query')])
@rate_limit(burst_size=4)
async def beer_search(message, query):
    """
    Search for a beer using brewerydb.com.

    Example::

        beer indian pale ale

    Response::

        Amnesia I.P.A.
        ABV: 7.2%
        IBU: 55
        Style: American-Style India Pale Ale
        Description: Named for the beer that was shipped to Her Majesty’s [...]

    """
    r = await http.get("http://api.brewerydb.com/v2/search", params={
        "q": query,
        "type": "beer",
        "key": api_key()
    })

    results = SafeStructure(r.json())
    beer = results.data[0]

    if not beer:
        raise CommandError("Beer not found on brewerydb.com.")

    props = [
        ('Name', beer.name)
    ]

    if results.abv:
        props.append(("ABV", results.abv))
    if results.ibu:
        props.append(("IBU", results.ibu))
    if beer.style:
        props.append(("Style", beer.style.name.strip()))
    if beer.description:
        props.append(("Description", beer.description.strip()))
    if beer.foodPairings:
        props.append(("Food pairings", beer.foodPairings.strip()))

    return build_mapping(props)
