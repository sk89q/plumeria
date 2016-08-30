#
# This is an example plugin that isn't bundled inside Plumeria.
# Add "example_plugin" to the list of plugins in your config file to
# load this plugin. Plugins can be regular Python packages and do not
# need to be inside this plugins directory.
#

from plumeria.command import commands
from plumeria.util.ratelimit import rate_limit


@commands.register('example', category='Fun')
@rate_limit()
async def example(message):
    """
    This is an example plugin.

    """
    return "Hello world"
