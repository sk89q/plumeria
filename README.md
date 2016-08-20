# Plumeria

Plumeria is a Discord bot used on the [SKCraft](https://www.skcraft.com) Discord channel.

NOTE: Plumeria predates Discord's official API and currently does not support bot accounts yet.

Works on Windows, Mac OS X, and Linux.

## Highlights

* Python 3.5
* Asynchronous
* Extensible
* Command piping (`.tagtop rock | youtube`)
* Attachment ingress, piping, and egress (`.image plumes | fetchimage | blur | memetext meme text`)
* Command piping from and to other bots (`.tagtop rock | youtube | say .play`)
* Embedded web server
* Per server, per channel, per user, per command pipeline, per time period rate limiting
* Rudimentary protection against SSRF and server-side DNS rebinding attacks

## Usage

1. Install Python 3.5
2. Install requirements.txt (`pip install -r requirements.txt`)
3. `./bot.py --config path_to_config.ini`

A configuration file will be generated if one does not exist. Change the configuration and restart the bot.

All plugins are enabled by default, but selected plugins can be disabled by changing the configuration file :

```ini
[plugins]
plumeria.plugins.steamid = True
plumeria.plugins.discord_transport = True
plumeria.plugins.usgs = False
plumeria.plugins.figlet = False
...
```

RethinkDB is required for the aliases module.

## Writing Plugins

### Overview

Everything is powered by events, including startup. The connection to Discord is a regular plugin and the actual connection is made during the init event. All messages are received via events.

Commands could be handled manually via the message events but instead there's a command manager helper that already parses for commands and takes on registrations.

### Discovery

Discovery looks for modules in `plumeria.plugins` package. The discovery code is in `bot.py` if you want to add support for modules outside this directory.

Plugins can intentionally not be enabled or disabled after the bot has started up.

### Getting Configuration

```python
from plumeria import config

api_key = config.create("example", "key",
                        fallback="unset",
                        comment="An API key from example.com") 
```

That call will register the configuration setting and also write the fallback to the user's configuration file during Plumeria startup. If no fallback is specified, then no value will be written.

To actually get the value of the configuration, you call the object (`api_key()`).

### Handling Startup

There are two main events: `preinit` and `init`. The Discord connecton is made during the `init` event (from the discord_transport plugin) and the web server is also started.

```python
from plumeria.event import bus

@bus.event("init")
async def init():
    await app.run(host=webserver_host(), port=webserver_port())
```

### Registering a Command

Commands are registered against the command manager.

```python
from plumeria.command import commands

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

Return values can be strings or `Response` objects if you want to provide attachments.

#### Responding with Attachments

```python
from PIL import Image
from plumeria.message import ImageAttachment, Response

im = Image.open("lena.ppm")
return Response("", attachments=[ImageAttachment(im, "example.png)])
```

#### Reading Attachments

To read attachments received (either from the user or from a piped command), simply look for attachments on the incoming message object:

```python
async def read_image(message):
    for attachment in message.attachments:
        try:
            if isinstance(attachment, ImageAttachment):
                return attachment
            elif attachment.mime_type.startswith("image/"):
                im = Image.open(io.BytesIO(await attachment.read()))
                return ImageAttachment(im, attachment.filename)
        except IOError as e:
            pass
    return await locator.first_value("message.read_image", message)
```

The method seen above helps with reading image files from attachments, because they could be of a wide assortment of image types, including the internal type provided by PIL/Pillow (the Python image manipulatipn library) if the image came from a piped command.

You can find that method in `plumeria.message`:

```python
from plumeria.message import read_image

attachment = await read_image(message)
```

#### Wildcard Command Matching

It's also possible to register a "wildcard" command interceptor (i.e. for aliases):

```python
from plumeria.command import commands

@commands.enumerator
async def alias_enumerator(server_id):
    if server_id:
        return aliases.get_mappings(server_id)
    else:
        return []


@commands.intercept
async def alias_listener(message, value, depth):
    if not message.channel.is_private:  # public channels only
        value = aliases.match_command(message, value)
        if value:
            message = ProxyMessage(message)
            message.content = value
            return await commands.execute(message, Context(), expect_prefix=False)
        return False
```

The purpose of the enumerator is really for the `help` module. The intercept callback is what handles commands.

#### Need Something More?

You can also listen to the message event directly (explained below) and handle commands yourself, though you would lose support for command chaining unless you implemented it yourself.

Because the command manager consumes the message event like any other plugin, you can just have your event handler run at a higher priority.

### Listening for Discord Events

Not all Discord events are yet sent to the bus but a few available include:

* channel.delete
* server.remove
* message
* self_message

Adding a new event is easy in `discord_transport.py`:

```python
@client.event
async def on_channel_delete(channel):
    await bus.post("channel.delete", DiscordChannel(channel))
```

The goal is to wrap all Discord objects with Plumeria's to allow the addition of helper methods and to (only theoretically at this point) support other transports like Skype or IRC.

Registering an event handler is like registering one for the initialization events:

```python
from plumeria.event import bus

@bus.event("channel.delete")
async def on_channel_delete(channel):
    if channel.server.id in history:
        if channel.id in history[channel.server.id]:
            del history[channel.server.id][channel.id]


@bus.event("server.remove")
async def on_server_remove(server):
    if server.id in history:
        del history[server.id]


@bus.event("message")
@bus.event("self_message")
async def on_message(message):
    channel = message.channel
    history[channel.server.id][channel.id].read(message)
```

### Registering a Web Server Page

The web server is powered by `aiohttp` and there's a very rudimentary Flask-like API in Plumeria.

Templates are powered by Jinja.

```python
from plumeria.webserver import app, render_template

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

### Performing Background Tasks

Start any background tasks in the `preinit` or `init` events. You can either run those background tasks in the asyncio event loop or in a thread, but remember to be careful whenever passing between those two contexts.

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
