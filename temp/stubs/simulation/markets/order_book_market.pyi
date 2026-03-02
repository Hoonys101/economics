import logging
from _typeshed import Incomplete
from dataclasses import dataclass
from modules.market.api import CanonicalOrderDTO, IIndexCircuitBreaker as IIndexCircuitBreaker, IPriceLimitEnforcer as IPriceLimitEnforcer, MarketConfigDTO, OrderTelemetrySchema
from simulation.core_markets import Market as Market
from simulation.markets.matching_engine import OrderBookMatchingEngine as OrderBookMatchingEngine
from simulation.models import Order as Order, Transaction as Transaction
from typing import Any

logger: Incomplete

@dataclass
class MarketOrder:
    """Internal mutable representation of an order in the order book."""
    agent_id: int | str
    side: str
    item_id: str
    quantity: float
    price_pennies: int
    price: float
    original_id: str
    target_agent_id: int | None = ...
    brand_info: dict[str, Any] | None = ...
    @classmethod
    def from_dto(cls, dto: CanonicalOrderDTO) -> MarketOrder: ...
    @property
    def order_type(self) -> str: ...
    def to_dto(self, market_id: str) -> CanonicalOrderDTO:
        """Converts internal MarketOrder to public immutable CanonicalOrderDTO."""

class OrderBookMarket(Market):
    """호가창(Order Book) 기반의 시장을 시뮬레이션하는 클래스.

    매수/매도 주문을 접수하고, 가격 우선 및 시간 우선 원칙에 따라 주문을 매칭하여 거래를 체결합니다.
    """
    id: Incomplete
    config_dto: Incomplete
    daily_avg_price: dict[str, float]
    daily_total_volume: dict[str, float]
    last_traded_prices: dict[str, float]
    last_trade_ticks: dict[str, int]
    cached_best_bid: dict[str, float]
    cached_best_ask: dict[str, float]
    last_tick_supply: float
    last_tick_demand: float
    circuit_breaker: Incomplete
    enforcer: Incomplete
    matching_engine: Incomplete
    def __init__(self, market_id: str, config_dto: MarketConfigDTO | None = None, logger: logging.Logger | None = None, enforcer: IPriceLimitEnforcer | None = None, circuit_breaker: IIndexCircuitBreaker | None = None) -> None:
        """OrderBookMarket을 초기화합니다.

        Args:
            market_id (str): 시장의 고유 ID (예: 'goods_market', 'labor_market').
            config_dto (MarketConfigDTO, optional): Market Configuration DTO.
            logger (logging.Logger, optional): 로깅을 위한 Logger 인스턴스. 기본값은 None.
            enforcer (IPriceLimitEnforcer, optional): 주입된 가격 제한 집행기.
            circuit_breaker (IIndexCircuitBreaker, optional): 주입된 시장 전체 서킷 브레이커.
        """
    @property
    def price_history(self) -> dict[str, Any]:
        """Exposes price history for signals/orchestration."""
    @property
    def buy_orders(self) -> dict[str, list[CanonicalOrderDTO]]:
        """Returns active buy orders as immutable CanonicalOrderDTOs."""
    @property
    def sell_orders(self) -> dict[str, list[CanonicalOrderDTO]]:
        """Returns active sell orders as immutable CanonicalOrderDTOs."""
    def clear_orders(self) -> None:
        """현재 틱의 모든 주문을 초기화합니다. 초기화 전 Best Bid/Ask를 캐싱합니다."""
    def cancel_orders(self, agent_id: str) -> None:
        """
        Cancels all orders for the specified agent.
        Iterates through buy and sell orders and removes any belonging to the agent.
        """
    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int):
        """시장에 주문을 제출합니다. 매칭은 별도의 메서드로 처리됩니다.
        WO-IMPL-MARKET-POLICY: Checks PriceLimitEnforcer and CircuitBreaker before accepting.

        Args:
            order_dto (CanonicalOrderDTO): 제출할 주문 객체.
            current_time (int): 현재 시뮬레이션 틱 (시간) 입니다.
        """
    def match_orders(self, current_time: int) -> list[Transaction]:
        """
        현재 틱의 모든 주문을 매칭하고 거래를 실행합니다.
        각 아이템별로 주문 매칭을 수행합니다.
        """
    def get_best_ask(self, item_id: str) -> float | None:
        """주어진 아이템의 최저 판매 가격(best ask)을 반환합니다."""
    def get_best_bid(self, item_id: str) -> float | None:
        """주어진 아이템의 최고 구매 가격(best bid)을 반환합니다."""
    def get_last_traded_price(self, item_id: str) -> float | None:
        """주어진 아이템의 마지막 체결 가격을 반환합니다."""
    def get_price(self, item_id: str) -> float:
        """
        Returns the current market price for the given item (IMarket Implementation).
        Returns last traded price or 0.0 if not available.
        """
    def get_last_trade_tick(self, item_id: str) -> int | None:
        """Returns the tick of the last trade for the item."""
    def get_spread(self, item_id: str) -> float | None:
        """주어진 아이템의 매도-매수 스프레드를 반환합니다."""
    def get_market_depth(self, item_id: str) -> dict[str, int]:
        """주어진 아이템의 매수/매도 주문 건수를 반환합니다."""
    def get_order_book_status(self, item_id: str) -> dict[str, Any]:
        """주어진 아이템의 현재 호가창 상태를 반환합니다."""
    def get_all_bids(self, item_id: str) -> list[MarketOrder]:
        """주어진 아이템의 모든 매수 주문을 반환합니다."""
    def get_all_asks(self, item_id: str) -> list[MarketOrder]:
        """주어진 아이템의 모든 매도 주문을 반환합니다."""
    def get_total_demand(self) -> float:
        """시장의 모든 매수 주문 총량을 반환합니다."""
    def get_total_supply(self) -> float:
        """시장의 모든 매도 주문 총량을 반환합니다."""
    def get_daily_avg_price(self) -> float:
        """
        해당 시장의 일일 평균 거래 가격을 반환합니다.
        매칭된 거래가 없으면 0.0을 반환합니다.
        """
    def get_daily_volume(self) -> float:
        """
        해당 시장의 일일 거래량을 반환합니다.
        """
    def get_telemetry_snapshot(self) -> list[OrderTelemetrySchema]:
        """Returns Pydantic schemas for UI consumption."""
    def set_reference_price(self, price: int) -> None:
        """
        Updates the enforcer's reference price.
        Called by TickOrchestrator or Market orchestrator.
        """
