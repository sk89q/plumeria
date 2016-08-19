import collections
import logging

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self.subscribers = collections.defaultdict(lambda: set())

    def subscribe(self, event, handler):
        self.subscribers[event].add(handler)

    def event(self, event):
        def decorator(f):
            self.subscribe(event, f)
            return f

        return decorator

    async def post(self, event, *args, **kwargs):
        for handler in self.subscribers[event]:
            try:
                await handler(*args, **kwargs)
            except:
                logging.warning("Error thrown in event handler for event '{}'".format(event), exc_info=True)


bus = EventBus()
