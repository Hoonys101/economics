from typing import Dict, List, Any
import logging
from modules.system.event_bus.api import IEventBus, EventHandler, E

logger = logging.getLogger(__name__)

class EventBus(IEventBus[E]):
    """
    A simple, synchronous implementation of the EventBus.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler[E]]] = {}

    def subscribe(self, event_type: str, handler: EventHandler[E]) -> None:
        """Subscribes a handler to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"EventBus: Subscribed handler to {event_type}")

    def publish(self, event: E) -> None:
        """
        Publishes an event to all subscribed handlers.
        """
        event_type = None
        if isinstance(event, dict):
            event_type = event.get('event_type')
        elif hasattr(event, 'event_type'):
            event_type = getattr(event, 'event_type')

        if not event_type:
            logger.error(f"EventBus: Published event without 'event_type': {event}")
            return

        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"EventBus: Error in handler for {event_type}: {e}", exc_info=True)
