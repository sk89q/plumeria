Tutorial
========

Let's start our first plugin! Create a new file in the **plugins** folder and name it :code:`my_first_plugin.py`.

Your First Command
------------------

We're going to create a new :code:`fetch` command that downloads the content of a webpage.

.. code-block:: python

    import re
    from plumeria.command import commands, CommandError

    @commands.register("fetch", "download", "get page", category="Utility")
    async def fetch(message):
        """
        Fetches a webpage.

        Example::

            /fetch http://www.google.com

        """
        q = message.content.strip()
        if not re.search("^https://", re.I): # naive URL checking
            raise CommandError("That's not a valid URL")
        # more to come

A command is created by decorating a function with :code:`commands.register()`, which takes a list of aliases. Spaces are acceptable characters in aliases and can be used to create sub-commands. A category is required for the help page so related commands are grouped together to make them easier to find. The actual name of the function doesn't matter, but there can only be one parameter, which is the message object that contains information about what was sent and who sent it.

Docstrings are shown on the help page for commands and they should be formatted in reStructuredText, and example of a docstring can be seen above. Docstrings in Python are surrounded by three quotation marks (""") and appear first in a function or object.

Fetching URLs
-------------

Because Plumeria is written to be asynchronous, we'll use the :code:`aiohttp` library to make HTTP requests. To improve security, we'll use the :code:`DefaultClientSession` object that comes with Plumeria.

.. code-block:: python


    import re
    from plumeria.command import commands, CommandError
    from plumeria.util.http import DefaultClientSession

    @commands.register("fetch", "download", "get page", category="Utility")
    async def fetch(message):
        """
        Fetches a webpage.

        Example::

            /fetch http://www.google.com

        """
        url = message.content.strip()
        if not re.search("^https://", re.I): # naive URL checking
            raise CommandError("That's not a valid URL")

        with DefaultClientSession() as session:
            async with session.get(url) as resp:
                if require_success and resp.status != 200:
                    raise CommandError("HTTP code is not 200; got {}".format(resp.status))
                return await resp.text()

We return text directly from the :code:`fetch()` method, which is assumed to be Markdown. If we want to return a message with attachments or other bells and whistles, we would need to return a :py:class:`plumeria.message.Response` object rather than a string, but that will be explained later.

To see how the HTTP client is used, see `the documentation for aiohttp <http://aiohttp.readthedocs.io/en/stable/client.html>`_.

.. tip::
    The function above is prefixed with *async*, which means that it is willing to give up control of the currently running "thread" so that something else can run. Python will manage what else will run for you, but you inform Python that you want to give up control by *awaiting* another function. In the example above, the function awaits the :code:`session.request()` function (in the form of the :code:`async with`) because requesting a webpage requires waiting for a remote server to respond, and then further on, the code awaits :code:`resp.text()` because the other's server response must be fully received.

Running Your Plugin
-------------------

If you have plugins in the **plugins** folder, Plumeria will be able to pick them up, but you still have to tell Plumeria to load your plugin. Open up your configuration file and add the following to the :code:`[plugins]` section:

.. code-block:: ini

    my_first_plugin = True

Restart Plumeria and see if your new plugin is loaded in the log, and then try the :samp:`.fetch https://github.com/sk89q/Plumeriae` command.

Adding Configuration
--------------------

Configuration can be declared at the top of a file using :code:`config.create()`, which returns a :py:class:`plumeria.config.Setting` object that can be used to read the value from the configuration at a later point.

.. code-block:: python

    from plumeria import config

    timeout = config.create("my_first_plugin", "fetch_timeout9", type=int, fallback=4,
                            comment="The maximum amount of time to wait for a webpage to load")

When the value of :code:`timeout` is required, simply call the object:

.. code-block:: python

    timeout()

.. warning::

    Configuration data can change while Plumeria is running.

We'll integrate this timeout into our command:

.. code-block:: python

    import re
    from plumeria import config
    from plumeria.command import commands, CommandError
    from plumeria.util.http import DefaultClientSession

    timeout = config.create("my_first_plugin", "fetch_timeout9", type=int, fallback=4,
                            comment="The maximum amount of time to wait for a webpage to load")

    @commands.register("fetch", "download", "get page", category="Utility")
    async def fetch(message):
        """
        Fetches a webpage.

        Example::

            /fetch http://www.google.com

        """
        url = message.content.strip()
        if not re.search("^https://", re.I): # naive URL checking
            raise CommandError("That's not a valid URL")

        with DefaultClientSession() as session:
            async with session.get(url, timeout=timeout()) as resp:
                if require_success and resp.status != 200:
                    raise CommandError("HTTP code is not 200; got {}".format(resp.status))
                return await resp.text()

Rate Limiting
-------------

To reduce abuse, we will want to limit how often the command can be used. There are two types of rate limits:

* A command cost, which is used to determine how many commands can be chained together
* A rate limit, which simply controls the rate of calls

By default, all commands have a cost of 1.0. Commands that have minimal CPU and network impact should have lower costs. Costs can be adjusted when registering the command:

.. code-block:: python

    @commands.register("fetch", "download", "get page", category="Utility", cost=1.0)

For our fetch command, we won't adjust the cost.

However, we do want to reduce how frequently the command can be used, so we'll apply a rate limit. Rate limits are per-user, per-channel, and per-server. Rate limits are simply added by applying a :code:`@rate_limit()` decorator.

.. code-block:: python

    from plumeria.util.ratelimit import rate_limit

    @commands.register("fetch", "download", "get page", category="Utility")
    @rate_limit()
    async def fetch(message):
        # etc.

Rate limits can be adjusted by changing burst size and fill rate:

.. code-block:: python

    @commands.register("fetch", "download", "get page", category="Utility")
    @rate_limit(burst_size=10, fill_rate=0.5)
    async def fetch(message):
        # etc.

.. warning::

    :code:`@rate_limit()` must appear **after** the command registration.
