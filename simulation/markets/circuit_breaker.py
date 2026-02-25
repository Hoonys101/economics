from collections import deque
import math
import logging
from typing import Optional, Dict, Tuple, Any
from modules.market.api import ICircuitBreaker

class DynamicCircuitBreaker(ICircuitBreaker):
    """
    Dynamic Circuit Breaker with temporal relaxation logic.
    Implements ICircuitBreaker protocol.
    """
    def __init__(self, config_module: Any = None, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger or logging.getLogger(__name__)
        self.price_history: Dict[str, deque] = {}

    def update_price_history(self, item_id: str, price: float) -> None:
        """Update the sliding window of price history."""
        window_size = getattr(self.config_module, "PRICE_VOLATILITY_WINDOW_TICKS", 20) if self.config_module else 20

        if item_id not in self.price_history:
            self.price_history[item_id] = deque(maxlen=window_size)
        elif self.price_history[item_id].maxlen != window_size:
            # Resize if config changed
            self.price_history[item_id] = deque(self.price_history[item_id], maxlen=window_size)

        self.price_history[item_id].append(price)

    def get_dynamic_price_bounds(self, item_id: str, current_tick: int, last_trade_tick: int) -> Tuple[float, float]:
        """
        Calculate adaptive price bounds based on volatility.
        Formula: Bounds = Mean * (1 ± (Base_Limit * Volatility_Adj))
        Volatility_Adj = 1 + (StdDev / Mean)

        Temporal Relaxation:
        Relaxation = (current_tick - last_trade_tick - timeout) * rate
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

        variance = sum((p - mean_price) ** 2 for p in history) / len(history)
        std_dev = math.sqrt(variance)

        volatility_adj = 1.0 + (std_dev / mean_price)
        base_limit = getattr(self.config_module, "MARKET_CIRCUIT_BREAKER_BASE_LIMIT", 0.15) if self.config_module else 0.15

        effective_limit = base_limit * volatility_adj

        lower_bound = mean_price * (1.0 - effective_limit)
        upper_bound = mean_price * (1.0 + effective_limit)

        # Temporal Relaxation
        if last_trade_tick is not None and last_trade_tick >= 0:
            relaxation_rate = getattr(self.config_module, "CIRCUIT_BREAKER_RELAXATION_PER_TICK", 0.05) if self.config_module else 0.05
            timeout = getattr(self.config_module, "CIRCUIT_BREAKER_TIMEOUT_TICKS", 10) if self.config_module else 10

            ticks_since = current_tick - last_trade_tick

            if ticks_since > timeout:
                relaxation = (ticks_since - timeout) * relaxation_rate
                lower_bound -= relaxation
                upper_bound += relaxation

                # Log periodically
                if (ticks_since - timeout) % 10 == 0:
                     self.logger.info(
                         f"CIRCUIT_BREAKER_RELAXATION | Item: {item_id}, Ticks Since Trade: {ticks_since}, Relaxation: {relaxation:.2f}",
                         extra={"tick": current_tick, "item_id": item_id, "relaxation": relaxation}
                     )

        return max(0.0, lower_bound), upper_bound
