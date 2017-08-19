# Plumeria, the Discord bot

[![Documentation Status](https://readthedocs.org/projects/plumeria/badge/?version=latest)](http://plumeria.readthedocs.io/en/latest/?badge=latest)

Plumeria is madness distilled into a Discord bot. Sure, you can do things like search YouTube for a video, look up osu! stats, and do all those things, ***but*** 

...you can feed the output of one command into another!

1. You like a YouTube video? `.yt waterparks stupid`
2. Want to write on it? `.last | mb i like`
3. Really like it? Let's make it black and white! `.last | bw` 
4. Make it an emoji? `.last | add emoji :waterparks:`

What a terrible emoji. Let's make a new composition just with just Discord:

1. `.render <b style="background: red; color: white">=')</b>`
2. Oh yeah... make it an emoji! `.last | add emoji :imhappy:`

Let's make it personal! Let's say you have a private Spotify playlist named *70's classics* and you want to show everyone a random song from it:

1. `.spotify connect` (first, connect your account to Spotify -- a one time thing)
2. `.spotify pick 70's classics`
3. Whoa... that's a list... let's play one of those songs on YouTube: `.last | first | stripurl | yt`

Discord rocks! `.mt https://www.discordapp.com Discord | mb ROCKS!`

There's *very* flexible support for command prefixes: `.mt` works, but so does `. mt` (helpful on mobile keyboards), but also `. Mt` or `/mt`, `!mt`, and so on.

Plumeria is written in Python 3. Plumeria is designed to work on Windows, Mac OS X, and Linux.

![Plumeria Help](readme/help.png)

## For Da Nerds

Cool stuff for plugin authors:

* Everything is a plugin! Everything! Even Discord support :smile:
* Support for command names with spaces in them
* Embedded web server that you can hook into
* Built-in OAuth support (i.e. used by the Spotify plugin so people can link their accounts)
* Support for images is implicit... you just call `read_image()` and it could have been a user-uploaded image, a linked image, or an OpenGraph image embedded on a webpage

## Installation

To run Plumeria, see the [documentation](http://plumeria.readthedocs.io/en/latest/).

## Command List

**Alias**

* alias
* alias delete
* alias get
* alias export

**Configuration**

* set
* set channel
* unset
* unset channel
* config get
* config info
* config list
* config defaults

**Development**

* pypi
* packagist
* random user
* rubygems
* unicode escape
* unicode name
* unicode code

**Electronics**

* resistors

**Fun**

* figlet
* dudu
* 8ball
* roll
* choice
* coin
* group prob

**Games**

* minecraft status
* minecraft uuid
* minecraft body
* minecraft head
* minecraft face
* minecraft skin
* minecraft cape
* osu sig
* osu stats

**GitLab**

* gitlab url
* gitlab addtoken
* gitlab removetoken
* gitlab tokens
* gitlab subscribe
* gitlab unsubscribe
* gitlab subscriptions

**Graphing**

* graph
* digraph
* pie
* bar
* histogram

**Image**

* qrcode
* fetch image
* memetext
* memetext2
* drawtext
* blur
* edge enhance
* emboss
* find edges
* sharpen
* bw
* square
* bg
* make spray
* tex

**Inspection**

* avatar
* user
* icon
* server

**Management**

* emoji create
* emoji delete
* icon set

**Music**

* artist charts
* charts
* lyrics
* soundcloud
* lastfm
* lastfm tag
* lastfm artist
* spotify artist
* spotify track
* spotify album
* spotify discog
* spotify top

**Operations**

* push
* pop
* put
* get
* argparse

**SKCraft**

* servers
* upcoming
* balance

**Search**

* strawpoll
* strawpoll results
* earthquakes
* cheapshark
* image
* cve
* translate
* anime
* imdb
* woot
* youtube
* recipes
* latlng
* directions
* wolfram
* similar music
* similar movies
* similar shows
* similar books
* similar authors
* similar games
* beer
* subreddit
* reddit
* gravatar
* xkcd
* wallhaven
* urban
* stats
* abstract

**Servers**

* a2squery

**Statistics**

* mean
* median
* median low
* median high
* median grouped
* mode
* pstdev
* pvariance
* stdev
* variance

**Steam**

* steam id
* steam profile
* steam avatar
* steam id64
* steam id32
* steam status

**String**

* uuid
* dashuuid
* hexuuid
* upper
* lower
* rot13
* idna
* punycode
* base64
* base64dec
* md5
* sha1
* sha224
* sha256
* urlescape
* unurlescape
* length
* findurl
* stripurl
* strip
* extract
* first
* end
* key

**User Preferences**

* pref set
* pref unset
* pref get
* pref list
* pref defaults

**Utility**

* help
* commands dump
* uptime
* update
* join
* ifttt
* last text
* last image
* last url
* timestamp
* screenshot
* screenshot mobile
* render crop
* render full
* echo

## License

The project is licensed under the MIT license.
