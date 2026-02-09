from typing import Protocol, Callable, TypeVar, Generic, Any
from modules.events.dtos import FinancialEvent

# A generic event type, but we primarily use FinancialEvent for now
E = TypeVar('E')

# A handler for a given event type
EventHandler = Callable[[E], None]

class IEventBus(Protocol[E]):
    """
    A central mediator for publishing and subscribing to system events.
    """

    def subscribe(self, event_type: str, handler: EventHandler[E]) -> None:
        """
        Subscribes a handler to a specific event type.

        Args:
            event_type: The identifier for the event (e.g., "LOAN_DEFAULTED").
            handler: The function to be called when the event is published.
        """
        ...

    def publish(self, event: E) -> None:
        """
        Publishes an event to all subscribed handlers.
        The event object is expected to have an 'event_type' attribute
        or be a dictionary with an 'event_type' key.

        Args:
            event: The event object to be broadcast.
        """
        ...
