import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit

URL = "http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"


@commands.register("earthquakes", "quakes", category="Search")
@rate_limit()
async def earthquakes(message):
    """
    Get a list of recent M4.5+ earthquakes in the past day.
    """
    data = (await http.get(URL)).json()
    if len(data['features']):
        output = [i['properties']['title'] for i in data['features']]
        return Response("\n".join(output))
    else:
        raise CommandError("No earthquakes are available.")
