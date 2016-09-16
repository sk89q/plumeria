from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.command import add_doc
from plumeria.util.ratelimit import rate_limit
from plumeria.util.string import first_words

types = (
    ("music", ("music", "band", "bands"), "polar bear club"),
    ("movies", ("movies", "movie"), "no country for old men"),
    ("shows", ("shows", "show", "tv"), "breaking bad"),
    ("books", ("books", "book"), "harry potter"),
    ("authors", ("authors", "author", "writer", "writers"), "jane austen"),
    ("games", ("games", "game"), "space engineers"),
)

api_key = config.create("tastekid", "key",
                        fallback="",
                        comment="An API key from https://www.tastekid.com/account/api_access")

for e in types:
    def make_command(type, names, example):
        @commands.register(*map(lambda s: "similar {}".format(s), names), category="Search")
        @rate_limit()
        @add_doc("Search for similar {}.\n\nExample::\n\n    /similar {} {}\n\n".format(type, names[0], example))
        async def similar(message):
            q = message.content.strip()
            if not q:
                raise CommandError("Search term required!")
            r = await http.get("https://www.tastekid.com/api/similar", params=[
                ('k', api_key()),
                ('type', type),
                ('q', q),
                ('info', '1'),
            ])
            data = r.json()
            results = data['Similar']['Results']
            if len(results):
                def map_result(e):
                    if e['yID']:
                        desc = "<https://youtu.be/{}>".format(e['yID'])
                    elif e['wTeaser'] and len(e['wTeaser']) > 600:
                        desc = first_words(e['wTeaser'])
                    elif e['wUrl']:
                        desc = "<>".format(e['wUrl'])
                    else:
                        desc = "*no info*"

                    return "\u2022 **{name}:** {desc}".format(name=e['Name'], desc=desc)

                return "\n".join(map(map_result, results[:15]))
            else:
                raise CommandError("no matches")


    make_command(*e)
