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

    Example::

        /quakes

    Response::

        M 5.4 - 49km NNE of Visokoi Island, South Georgia
        M 4.9 - Owen Fracture Zone region
        M 4.6 - 9km W of Sarahan, India
        M 4.5 - 7km S of Sanchez, Dominican Republic
        M 4.7 - 157km NNE of Mohean, India
        M 4.5 - 139km NNW of Clyde River, Canada
        M 5.1 - 14km NNW of Santa Monica, Philippines
    """
    data = (await http.get(URL)).json()
    if len(data['features']):
        output = [i['properties']['title'] for i in data['features']]
        return Response("\n".join(output))
    else:
        raise CommandError("No earthquakes are available.")
