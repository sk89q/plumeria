# Plumeria, the Discord bot

[![Documentation Status](https://readthedocs.org/projects/plumeria/badge/?version=latest)](http://plumeria.readthedocs.io/en/latest/?badge=latest)

Plumeria is a fun and practical Discord bot and personal assistant for your Discord server.

* Easily find YouTube videos.
* Look up movies and get their synopsis and IMDB ratings.
* Lookup discography and music artists.
* Turn on the lights in your home with the IFTTT plugin.
* Create meme images on the fly.
* Get driving directions between two places.

Plumeria is written in Python 3. Plumeria is designed to work on Windows, Mac OS X, and Linux.

![Plumeria Help](readme/help.png)

## Examples

One cool feature you'll find in Plumeria is the ability to chain commands together.

Here are some examples of commands and command chaining:

* Searching the Internet for an image and overlaying text on it: 
  `.image skateboard | mt do this`
* Getting the top tracks for a music tag on last.fm and finding a YouTube video for it:
  `.tagtop rock | youtube`
* Choosing between several entries:
   `.choice pizza, burger, hot dogs | echo What's for dinner?`
* Email yourself the last message (requires setup on IFTTT):
  `.last | ifttt email`
* Drawing a pie graph of some Strawpoll.me results:
  `.results 18233 | pie`
* Generate a directed graph:
  `.digraph a -> b; b -> c`
* Change the server icon to a random image search using Bing for "flower":
  `.i flower | square | bg white | icon set`
* Render a webpage and then make it an emoji:
  `.render <link href="https://fonts.googleapis.com/css?family=Pacifico" rel="stylesheet"><body bgcolor=white style="font-family: Pacifico, Arial, sans-serif; font-size:30pt;color:purple">pretty</body> | add emoji pretty`

You can create aliases as well to reuse commands.

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
