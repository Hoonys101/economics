from modules.events.dtos import FinancialEvent as FinancialEvent
from typing import Callable, Protocol, TypeVar

E = TypeVar('E')
EventHandler = Callable[[E], None]

class IEventBus(Protocol[E]):
    """
    A central mediator for publishing and subscribing to system events.
    """
    def subscribe(self, event_type: str, handler: EventHandler[E]) -> None:
        '''
        Subscribes a handler to a specific event type.

        Args:
            event_type: The identifier for the event (e.g., "LOAN_DEFAULTED").
            handler: The function to be called when the event is published.
        '''
    def publish(self, event: E) -> None:
        """
        Publishes an event to all subscribed handlers.
        The event object is expected to have an 'event_type' attribute
        or be a dictionary with an 'event_type' key.

        Args:
            event: The event object to be broadcast.
        """
