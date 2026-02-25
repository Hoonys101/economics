from _typeshed import Incomplete
from modules.system.event_bus.api import E as E, EventHandler as EventHandler, IEventBus as IEventBus

logger: Incomplete

class EventBus(IEventBus[E]):
    """
    A simple, synchronous implementation of the EventBus.
    """
    def __init__(self) -> None: ...
    def subscribe(self, event_type: str, handler: EventHandler[E]) -> None:
        """Subscribes a handler to a specific event type."""
    def publish(self, event: E) -> None:
        """
        Publishes an event to all subscribed handlers.
        """
