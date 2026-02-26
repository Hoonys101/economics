from _typeshed import Incomplete
from modules.market.api import CanonicalOrderDTO as CanonicalOrderDTO, IMatchingEngine, MarketConfigDTO as MarketConfigDTO, MatchingResultDTO, OrderBookStateDTO as OrderBookStateDTO, StockMarketStateDTO as StockMarketStateDTO
from simulation.models import Transaction as Transaction

logger: Incomplete

class OrderBookMatchingEngine(IMatchingEngine):
    """
    Stateless matching engine for Goods and Labor markets.
    Implements price-time priority and targeted (brand loyalty) matching.
    Uses Integer Math (Pennies) for Zero-Sum Integrity.
    """
    def match(self, state: OrderBookStateDTO, current_tick: int, config: MarketConfigDTO | None = None) -> MatchingResultDTO: ...

class StockMatchingEngine(IMatchingEngine):
    """
    Stateless matching engine for Stock Market.
    Matches Buy and Sell orders for each firm.
    Uses Integer Math (Pennies).
    """
    def match(self, state: StockMarketStateDTO, current_tick: int, config: MarketConfigDTO | None = None) -> MatchingResultDTO: ...
