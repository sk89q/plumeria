import collections
import logging

logger = logging.getLogger(__name__)

VERY_EARLY = -100
EARLY = -50
NORMAL = 0
LATE = 50
VERY_LATE = 100

Handler = collections.namedtuple("Handler", "handler priority")


class ServiceLocator:
    def __init__(self):
        self.providers = collections.defaultdict(lambda: [])

    def register(self, service, handler, priority=NORMAL):
        self.providers[service].append(Handler(handler, priority))
        self.providers[service] = sorted(self.providers[service], key=lambda x: x.priority)

    def provide(self, service, priority=NORMAL):
        def decorator(f):
            self.register(service, f, priority)
            return f

        return decorator

    async def first_value(self, service, *args, **kwargs):
        for handler in self.providers[service]:
            value = await handler.handler(*args, **kwargs)
            if value:
                return value


locator = ServiceLocator()
