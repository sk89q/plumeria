from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit
import plumeria.util.http as http

api_key = config.create("brewerydb", "key",
                        fallback="unset",
                        comment="An API key from brewerydb.com")


@commands.register("beer", category="Search")
@rate_limit(burst_size=4)
async def beer_search(message):
    """DL
    Search for a beer using brewerydb.com.
    """
    query = message.content.strip()
    if len(query):
        r = await http.get("http://api.brewerydb.com/v2/search", params={
            "q": query,
            "type": "beer",
            "key": api_key()
        })
        results = r.json()
        if len(results['data']):
            beer = results['data'][0]
            lines = [beer['name']]
            if "abv" in beer: lines.append("ABV: {}%".format(beer["abv"]))
            if "ibu" in beer: lines.append("IBU: {}".format(beer["ibu"]))
            if "style" in beer:
                lines.append("Style: {}".format(beer["style"]["name"].strip()))
            if "description" in beer: lines.append("Description: {}".format(beer["description"].strip()))
            if "foodPairings" in beer: lines.append("Food pairings: {}".format(beer["foodPairings"].strip()))
            return Response("\n".join(lines))
    else:
        raise CommandError("No query term specified.")
