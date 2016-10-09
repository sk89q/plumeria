from plumeria import config
from plumeria.config.types import boolstr, dateformatstr

nsfw = config.create("common", "nsfw", type=boolstr, fallback=False, comment="Whether to allow NSFW functions",
                     scoped=True, private=False)

short_date_time_format = config.create("common", "date_time_short", type=dateformatstr,
                                       fallback="%b %m, %Y %I:%M %p %Z", comment="Short date and time format",
                                       scoped=True, private=False)
