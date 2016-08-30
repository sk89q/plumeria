# Extra Plugins

Plumeria plugins are regular Python modules and can be anywhere on your system as long as Plumeria can load it. However, this plugins directory is provided as another place where you can place plugins for loading into Plumeria.

To load a module as a plugin, add it to your configuration file:

```ini
[plugins]
your_plugin = True
```
