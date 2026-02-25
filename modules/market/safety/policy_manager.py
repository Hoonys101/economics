from typing import Dict, Any, Optional
from modules.market.api import IPriceLimitEnforcer, IIndexCircuitBreaker
from modules.market.safety_dtos import PriceLimitConfigDTO

class MarketSafetyPolicyManager:
    """
    Central registry for market safety policies.
    Allows dynamic updates to price limits and circuit breakers.
    """
    def __init__(self):
        self._enforcers: Dict[str, IPriceLimitEnforcer] = {}
        self._circuit_breakers: Dict[str, IIndexCircuitBreaker] = {}

    def register_enforcer(self, market_id: str, enforcer: IPriceLimitEnforcer) -> None:
        self._enforcers[market_id] = enforcer

    def register_circuit_breaker(self, market_id: str, breaker: IIndexCircuitBreaker) -> None:
        self._circuit_breakers[market_id] = breaker

    def update_price_limit_config(self, market_id: str, config: PriceLimitConfigDTO) -> bool:
        if market_id in self._enforcers:
            self._enforcers[market_id].update_config(config)
            return True
        return False
