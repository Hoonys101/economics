from typing import Dict, Any, Optional
import logging

from modules.market.api import IIndexCircuitBreaker, IndexCircuitBreakerConfigDTO

class IndexCircuitBreaker(IIndexCircuitBreaker):
    def __init__(self, config: IndexCircuitBreakerConfigDTO, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._is_halted = False
        self._halt_until_tick = 0
        self._current_level = 0
        self._reference_index = 0.0

    def check_market_health(self, market_stats: Dict[str, Any], current_tick: int) -> bool:
        """
        Evaluates overall market health statistics to determine if a halt is required.
        Updates internal halt state safely.
        Returns True if healthy (trading continues), False if a halt is triggered.
        """
        # 1. Evaluate existing halt duration
        if self._is_halted:
            if self._halt_until_tick != float('inf') and current_tick >= self._halt_until_tick and self._current_level < 3:
                self.logger.info(f"CIRCUIT_BREAKER | Halt lifted at tick {current_tick}. Level {self._current_level} cleared.")
                self._is_halted = False
                # Do not reset _current_level to avoid re-triggering same level in same session
            else:
                return False # Still halted

        # 2. Extract current index value (e.g., composite price index)
        current_index = market_stats.get('market_index')
        if current_index is None:
            return True # Cannot evaluate reliably, assume healthy to prevent false halts

        if self._reference_index <= 0:
            return True # Avoid division by zero

        # 3. Calculate drop percentage
        drop_pct = (self._reference_index - current_index) / self._reference_index

        # 4. Step-wise threshold evaluation
        if drop_pct >= self.config.threshold_level_3 and self._current_level < 3:
            self._trigger_halt(3, float('inf'), current_tick, current_index)
            return False
        elif drop_pct >= self.config.threshold_level_2 and self._current_level < 2:
            self._trigger_halt(2, self.config.halt_duration_level_2, current_tick, current_index)
            return False
        elif drop_pct >= self.config.threshold_level_1 and self._current_level < 1:
            self._trigger_halt(1, self.config.halt_duration_level_1, current_tick, current_index)
            return False

        return True

    def _trigger_halt(self, level: int, duration: float, current_tick: int, current_index: float) -> None:
        self._is_halted = True
        self._current_level = level
        self._halt_until_tick = current_tick + duration if duration != float('inf') else float('inf')

        drop_pct = (self._reference_index - current_index) / self._reference_index

        self.logger.warning(
            f"CIRCUIT_BREAKER | Market Halted! Level {level} triggered. Drop: {drop_pct:.2%}. Halting until {self._halt_until_tick}",
            extra={
                'tick': current_tick,
                'level': level,
                'halt_until': self._halt_until_tick,
                'reference_index': self._reference_index,
                'current_index': current_index,
                'drop_pct': drop_pct
            }
        )

    def is_active(self) -> bool:
        return self._is_halted

    def set_reference_index(self, index_value: float) -> None:
        """
        Sets the baseline index value used to calculate the drop percentage.
        Resets the circuit breaker state for a new session.
        """
        if index_value > 0:
            self._reference_index = index_value
            self._is_halted = False
            self._current_level = 0
            self._halt_until_tick = 0
