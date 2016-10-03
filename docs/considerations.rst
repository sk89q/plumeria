Considerations
==============

Plumeria is best run from some sort of dedicated server, either at home or in a proper data center, that is on a fast Internet connection. However, Plumeria will also work on your home computer, though perhaps not as quickly.

.. tip::

    As of writing, students can get a year of free VPS hosting by signing up for the `GitHub education pack <https://education.github.com/pack>`_.

Regardless of your choice, there are some considerations to keep in mind when hosting Plumeria — or any kind of bot.

* The bot will utilize CPU when it is invoked. Most commands won't use any appreciable processing power, but, for example, the image commands could (for brief amounts of time).
* If the system running the bot does not have a good Internet connection, some commands (image downloading-related) could saturate the connection. It also means that the bot will respond slowly.
* The public of the IP of the system running the bot can be exposed. This is merely a consequence of features like image fetching.
* Any sort of bot, application, or website that lets people fetch URLs is susceptible to a problem called Server-Side Request Forgery (SSRF). For example, normally your router's website can't be accessed from outside the Internet, but a program running on your computer would be considered on the inside. Fortunately, Plumeria does have protection in the form of checking where names and addresses resolve to, but this protection doesn't extend to certain plugins that invoke outside programs (like the website capture plugin).
