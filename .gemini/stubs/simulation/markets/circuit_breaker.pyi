import logging
from _typeshed import Incomplete
from collections import deque
from modules.market.api import CanonicalOrderDTO as CanonicalOrderDTO, ICircuitBreaker, IPriceLimitEnforcer
from modules.market.safety_dtos import PriceLimitConfigDTO, ValidationResultDTO
from typing import Any

class PriceLimitEnforcer(IPriceLimitEnforcer):
    """
    Stateless enforcer for price limits.
    Strictly adheres to the Penny Standard (int).
    """
    def __init__(self, config: PriceLimitConfigDTO | None = None) -> None: ...
    def update_config(self, config: PriceLimitConfigDTO) -> None: ...
    def set_reference_price(self, price: int) -> None: ...
    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO: ...

class DynamicCircuitBreaker(ICircuitBreaker):
    """
    Legacy adapter wrapping PriceLimitEnforcer.
    Maintains SMA state for backward compatibility but delegates validation.
    """
    config_module: Incomplete
    logger: Incomplete
    price_history: dict[str, deque]
    enforcer: Incomplete
    def __init__(self, config_module: Any = None, logger: logging.Logger | None = None) -> None: ...
    def update_price_history(self, item_id: str, price: float) -> None:
        """Update the sliding window of price history."""
    def get_dynamic_price_bounds(self, item_id: str, current_tick: int, last_trade_tick: int) -> tuple[float, float]:
        """
        Legacy float bounds return. Relaxation logic removed.
        """
    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO: ...
    def set_reference_price(self, price: int) -> None: ...
    def update_config(self, config: PriceLimitConfigDTO) -> None: ...
