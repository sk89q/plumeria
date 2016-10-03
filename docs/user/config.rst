Configuration
=============

Without any extra parameters, Plumeria will use :code:`config.ini` to store configuration. If the file doesn't exist, then Plumeria will create it. Plumeria will update a configuration file with new values on start.

You can edit this configuration file with any text editor. Windows users may want to use an editor like `Notepad++ <https://notepad-plus-plus.org/download/v7.html>`_ for more editing features like longer undo history.

Rather than :code:`config.ini`, a different configuration file can be used by passing it as an argument:

.. code-block:: console

./plumeria-bot.py --config something_else.ini

Enabling Plugins
----------------

If no plugins are enabled (which is the case if the configuration file has just been created), the only content of the file will be a section to control which plugins are to be loaded:

.. code-block:: ini

[plugins]
plumeria.plugins.message_ops = True
plumeria.plugins.figlet = True
plumeria.plugins.string = False
plumeria.plugins.webserver = True
plumeria.plugins.memetext = False
plumeria.plugins.imdb = True
plumeria.plugins.gravatar = True
# and so on

You can change entries to :code:`True` to turn on the plugin and :code:`False` to turn off the plugin.

If you have no plugins enabled, Plumeria will start but it will sit and do nothing.

Plugin Configuration
--------------------

Most plugins will have some extra configuration for you to change. However, configuration for a plugin will only be added to your file when the plugin is loaded, so you have to enable the plugin and then (re)start Plumeria to see those settings.

For example, until you actually enable the Discord transport plugin and then run Plumeria, you wouldn't see the following section:

.. code-block:: ini

[discord]
# The Discord token to login with (overrides password login if set)
token =
# The Discord password to login with
password =
# The Discord username to login to
username =

Permissions
-----------

Bot Administrators
~~~~~~~~~~~~~~~~~~

A few commands are available only to users deemed "bot administrators."

To add yourself as a bot administrator, you will first need to find you Discord user ID. One way to find your user ID is to go to your Discord account settings, "Appearance," and check "Developer Mode" to allow you to right click yourself and choose "Copy ID." Once you have your ID, add it to your configuration file in the following section:

.. code-block:: ini

        [perms]
        admin_users = 0000000000000000

Server Administrators
~~~~~~~~~~~~~~~~~~~~~

Some functions, like creating server aliases, is limited to users deemed "server bot administrators."

Users are identified by having a role named :code:`bot-admin` on a particular server.
