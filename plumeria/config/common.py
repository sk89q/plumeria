from plumeria import config
from plumeria.config import boolstr

nsfw = config.create("common", "nsfw", type=boolstr, fallback=False, comment="Whether to allow NSFW functions",
                     scoped=True, private=False)
