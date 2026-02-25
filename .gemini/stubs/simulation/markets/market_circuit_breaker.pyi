import logging
from _typeshed import Incomplete
from modules.market.api import IIndexCircuitBreaker, IndexCircuitBreakerConfigDTO as IndexCircuitBreakerConfigDTO
from typing import Any

class IndexCircuitBreaker(IIndexCircuitBreaker):
    config: Incomplete
    logger: Incomplete
    def __init__(self, config: IndexCircuitBreakerConfigDTO, logger: logging.Logger | None = None) -> None: ...
    def check_market_health(self, market_stats: dict[str, Any], current_tick: int) -> bool:
        """
        Evaluates overall market health statistics to determine if a halt is required.
        Updates internal halt state safely.
        Returns True if healthy (trading continues), False if a halt is triggered.
        """
    def is_active(self) -> bool: ...
    def set_reference_index(self, index_value: float) -> None:
        """
        Sets the baseline index value used to calculate the drop percentage.
        Resets the circuit breaker state for a new session.
        """
