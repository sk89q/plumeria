import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit


@commands.register("abstract", "about", "define", category="Search")
@rate_limit()
async def abstract(message):
    """
    Create a short summary about a given topic.

    Uses DuckDuckGo to get the summary.

    Example::

        .about knuckle puck

    might return:

        Knuckle Puck is an American rock band from the south suburbs of Chicago, Illinois. The group started...

    """
    r = await http.get("https://api.duckduckgo.com/", params={
        "q": message.content,
        "format": "json",
    })
    data = r.json()
    if len(data['Abstract']):
        return Response(data['Abstract'])
    elif len(data['RelatedTopics']):
        return Response(data['RelatedTopics'][0]['Text'])
    else:
        raise CommandError("No information available.")
