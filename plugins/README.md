# Extra Plugins

You can put Python modules into this directory and then load them into Plumeria. However, plugins for Plumeria can simply be regular Python packages and do not need to be inside this directory.

To load a module as a plugin, add it to your configuration file:

```ini
[plugins]
your_plugin = True
```
