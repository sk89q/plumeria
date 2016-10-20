import collections
import logging

logger = logging.getLogger(__name__)

__all__ = ('EventBus',)


class EventBus:
    """Keeps track of event handlers and dispatches events to the handlers."""

    def __init__(self):
        self.subscribers = collections.defaultdict(lambda: set())

    def subscribe(self, event: str, handler: collections.Callable):
        """
        Add a function has a handler of an event.

        The arguments passed to the event handler function will depend on the
        code calling the event.

        Parameters
        ----------
        event : str
            The event name
        handler : Callable
            The function to call

        """
        self.subscribers[event].add(handler)

    def event(self, event):
        """
        Decorator to register events.

        .. code-block: python

            @event_bus.event('example')
            def event_handler(*args, **kwargs):
                pass

        Parameters
        ----------
        event : str
            The event name

        """

        def decorator(f):
            self.subscribe(event, f)
            return f

        return decorator

    async def post(self, event, *args, **kwargs):
        """
        Dispatches an event.

        Exceptions thrown by handlers are logged but do not stop event handling.

        Parameters
        ----------
        event : str
            The event name
        *args
            The arguments to pass to event handlers
        **kwargs
            The keyword arguments to pass to event handlers

        """

        for handler in self.subscribers[event]:
            try:
                await handler(*args, **kwargs)
            except Exception:
                logger.warning("Error thrown in event handler for event '{}'".format(event), exc_info=True)


bus = EventBus()
