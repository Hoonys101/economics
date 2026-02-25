from collections import deque
import math
import logging
from typing import Optional, Dict, Tuple, Any
from modules.market.api import ICircuitBreaker, IPriceLimitEnforcer, CanonicalOrderDTO
from modules.market.safety_dtos import PriceLimitConfigDTO, ValidationResultDTO
from modules.finance.api import FloatIncursionError

class PriceLimitEnforcer(IPriceLimitEnforcer):
    """
    Stateless enforcer for price limits.
    Strictly adheres to the Penny Standard (int).
    """
    def __init__(self, config: Optional[PriceLimitConfigDTO] = None):
        self._config: Optional[PriceLimitConfigDTO] = config
        self._reference_price: int = 0

    def update_config(self, config: PriceLimitConfigDTO) -> None:
        self._config = config

    def set_reference_price(self, price: int) -> None:
        if isinstance(price, float):
            raise FloatIncursionError(f"set_reference_price expects int, got float: {price}")
        self._reference_price = price

    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO:
        if not self._config or not self._config.is_enabled:
            return ValidationResultDTO(is_valid=True)

        if isinstance(order.price_pennies, float):
            raise FloatIncursionError(f"Order price_pennies must be int, got float: {order.price_pennies}")

        if self._config.mode == 'DYNAMIC':
            return self._validate_dynamic(order.price_pennies)
        elif self._config.mode == 'STATIC':
            return self._validate_static(order.price_pennies)

        return ValidationResultDTO(is_valid=True)

    def _validate_dynamic(self, price_pennies: int) -> ValidationResultDTO:
        if self._reference_price <= 0:
            # History-Free Discovery phase or invalid reference
            return ValidationResultDTO(is_valid=True)

        limit_margin = int(self._reference_price * self._config.base_limit)
        lower_bound = max(1, self._reference_price - limit_margin) # Floor at 1 penny
        upper_bound = self._reference_price + limit_margin

        if price_pennies < lower_bound:
            return ValidationResultDTO(is_valid=False, reason="PRICE_BELOW_DYNAMIC_FLOOR", adjusted_price=lower_bound)
        if price_pennies > upper_bound:
            return ValidationResultDTO(is_valid=False, reason="PRICE_ABOVE_DYNAMIC_CEILING", adjusted_price=upper_bound)

        return ValidationResultDTO(is_valid=True)

    def _validate_static(self, price_pennies: int) -> ValidationResultDTO:
        if self._config.static_floor is not None and price_pennies < self._config.static_floor:
            return ValidationResultDTO(is_valid=False, reason="PRICE_BELOW_STATIC_FLOOR", adjusted_price=self._config.static_floor)

        if self._config.static_ceiling is not None and price_pennies > self._config.static_ceiling:
            return ValidationResultDTO(is_valid=False, reason="PRICE_ABOVE_STATIC_CEILING", adjusted_price=self._config.static_ceiling)

        return ValidationResultDTO(is_valid=True)


class DynamicCircuitBreaker(ICircuitBreaker):
    """
    Legacy adapter wrapping PriceLimitEnforcer.
    Maintains SMA state for backward compatibility but delegates validation.
    """
    def __init__(self, config_module: Any = None, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger or logging.getLogger(__name__)
        self.price_history: Dict[str, deque] = {}

        # Initialize Enforcer Config from Legacy Config Module
        base_limit = getattr(self.config_module, "MARKET_CIRCUIT_BREAKER_BASE_LIMIT", 0.15) if self.config_module else 0.15

        # We assume DYNAMIC mode by default for legacy behavior
        enforcer_config = PriceLimitConfigDTO(
            id="legacy_adapter",
            is_enabled=True,
            mode='DYNAMIC',
            base_limit=base_limit
        )
        self.enforcer = PriceLimitEnforcer(config=enforcer_config)

    def update_price_history(self, item_id: str, price: float) -> None:
        """Update the sliding window of price history."""
        window_size = getattr(self.config_module, "PRICE_VOLATILITY_WINDOW_TICKS", 20) if self.config_module else 20

        if item_id not in self.price_history:
            self.price_history[item_id] = deque(maxlen=window_size)
        elif self.price_history[item_id].maxlen != window_size:
            # Resize if config changed
            self.price_history[item_id] = deque(self.price_history[item_id], maxlen=window_size)

        self.price_history[item_id].append(price)

        # Automatically update enforcer's reference price based on SMA
        # Note: Must convert float price to pennies when passing to enforcer
        history = list(self.price_history[item_id])
        if not history:
             return

        mean_price = sum(history) / len(history)
        mean_pennies = int(round(mean_price * 100))
        self.enforcer.set_reference_price(mean_pennies)

    def get_dynamic_price_bounds(self, item_id: str, current_tick: int, last_trade_tick: int) -> Tuple[float, float]:
        """
        Legacy float bounds return. Relaxation logic removed.
        """
        min_history_len = getattr(self.config_module, "CIRCUIT_BREAKER_MIN_HISTORY", 7) if self.config_module else 7

        # History-Free Discovery
        if item_id not in self.price_history or len(self.price_history[item_id]) < min_history_len:
            # self.logger.debug(f"History-Free Discovery: Widening bounds for {item_id}.")
            return 0.0, float('inf')

        history = list(self.price_history[item_id])
        mean_price = sum(history) / len(history)

        if mean_price <= 0:
            return 0.0, float('inf')

        # Use base_limit from config module or default to 0.15
        base_limit = getattr(self.config_module, "MARKET_CIRCUIT_BREAKER_BASE_LIMIT", 0.15) if self.config_module else 0.15

        # Calculate bounds using simple margin (No Volatility, No Relaxation)
        limit_margin = mean_price * base_limit
        lower_bound = max(0.01, mean_price - limit_margin) # Floor at 1 penny (0.01 dollars)
        upper_bound = mean_price + limit_margin

        return lower_bound, upper_bound

    def validate_order(self, order: CanonicalOrderDTO) -> ValidationResultDTO:
        # Before validating, we must ensure enforcer has correct reference price for THIS item.
        # Since Enforcer is single-state reference, we set it now.
        if order.item_id in self.price_history:
             history = list(self.price_history[order.item_id])
             if history:
                 mean_price = sum(history) / len(history)
                 mean_pennies = int(round(mean_price * 100))
                 self.enforcer.set_reference_price(mean_pennies)
             else:
                 self.enforcer.set_reference_price(0)
        else:
             self.enforcer.set_reference_price(0)

        return self.enforcer.validate_order(order)

    def set_reference_price(self, price: int) -> None:
        self.enforcer.set_reference_price(price)

    def update_config(self, config: PriceLimitConfigDTO) -> None:
        self.enforcer.update_config(config)
