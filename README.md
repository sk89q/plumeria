# Plumeria

Plumeria is a Discord bot used on the [SKCraft](https://www.skcraft.com) Discord channel.

NOTE: Plumeria predates Discord's official API and currently does not support bot accounts yet.

Works on Windows, Mac OS X, and Linux.

## The Good

* Python 3.5
* Asynchronous
* Extensible
* Command piping (`.tagtop rock | youtube`)
* Attachment ingress, piping, and egress (`.image plumes | fetchimage | blur | drawtext meme text`)
* Command piping from and to other bots (`.tagtop rock | youtube | say .play`)
* Embedded web server
* Per server, per channel, per user, per command pipeline, per time period rate limiting
* Rudimentary protection against SSRF and server-side DNS rebinding attacks
* Transport agnostic (can be used on IRC/Skype/etc.)

## The Bad

* Alias system needs rework
* A better persistence mechanism is needed
* Theoretically transport agnostic but not really

## The Ugly

* Plumeria isn't worked on very often
* No way yet to disable modules

## Usage

1. Install Python 3.5
2. Install requirements.txt (`pip install -r requirements.txt`)
3. `./bot.py --config path_to_config.ini`

A configuration file will be generated if one does not exist. Change the configuration and restart the bot.

## Writing Plugins

### A Command

```python
@commands.register("steamid", category="Steam")
@rate_limit()
async def steamid(message):
    """
    Look up variants of a Steam's user ID.
    """
    s = message.content.strip()
    id = await parse_steam_id(s)
    return "**ID64:** {}\n**ID32:** {}\n**URL:** {}".format(
        id.to_64(),
        id.to_text(),
        id.community_url(),
    )
```

### A Webpage

```python
@app.route('/help/{server}')
async def handle(request):
    server_id = request.match_info['server']
    if server_id == "private":
        server_id = None
    categories = set()
    by_category = collections.defaultdict(lambda: [])
    mappings = sorted(await commands.get_mappings(server_id), key=lambda m: m.command.category or "")
    for mapping in mappings:
        categories.add(mapping.command.category)
        by_category[mapping.command.category].append(mapping)
    categories = sorted(categories)
    return render_template("help.html", commands=mappings, by_category=by_category, categories=categories)

```

## Plugins

### Developed

* Alias
* BreweryDB
* Cheapshark
* DuckDuckGo
* Figlet
* Source Server Query (A2S)
* Help
* Image processing (fetch, blur, sharpen, etc.)
* IMDB
* Last.fm
* Minecraft
* QRCode
* Git update
* Statistics (mean, mode, etc.)
* Steam Community
* String manipulation (upper, lower, rot13, etc.)
* Time
* USGS
* UUIDs
* YouTube

### Planned

* Channel management
* VOIP event logging
* GitLab/GitHub hooks

### Low priority

* Twitch
* Music bot

## License

The project is licensed under the MIT license.
