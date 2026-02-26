import logging
from _typeshed import Incomplete
from dataclasses import dataclass
from modules.finance.api import IShareholderRegistry as IShareholderRegistry, IShareholderView as IShareholderView
from modules.market.api import CanonicalOrderDTO, IIndexCircuitBreaker as IIndexCircuitBreaker, OrderTelemetrySchema, StockMarketConfigDTO as StockMarketConfigDTO
from simulation.core_markets import Market as Market
from simulation.markets.matching_engine import StockMatchingEngine as StockMatchingEngine
from simulation.models import Order as Order, Transaction as Transaction
from typing import Any

logger: Incomplete

@dataclass
class ManagedOrder:
    """A mutable wrapper for an immutable CanonicalOrderDTO to manage its state within the order book."""
    order: CanonicalOrderDTO
    remaining_quantity: float
    created_tick: int

class StockMarket(Market):
    """
    주식 시장 클래스.
    
    기업 주식의 매수/매도 주문을 관리하고, 거래를 매칭합니다.
    주가는 기업 순자산가치(Book Value) 기반으로 기준가를 설정하고,
    실제 거래는 호가 매칭으로 이루어집니다.
    """
    id: str
    config_dto: Incomplete
    logger: Incomplete
    shareholder_registry: Incomplete
    index_circuit_breaker: Incomplete
    matched_transactions: list[Transaction]
    buy_orders: dict[int, list[ManagedOrder]]
    sell_orders: dict[int, list[ManagedOrder]]
    last_prices: dict[int, float]
    reference_prices: dict[int, float]
    daily_volumes: dict[int, float]
    daily_high: dict[int, float]
    daily_low: dict[int, float]
    matching_engine: Incomplete
    def __init__(self, config_dto: StockMarketConfigDTO, shareholder_registry: IShareholderRegistry, logger: logging.Logger | None = None, index_circuit_breaker: IIndexCircuitBreaker | None = None) -> None: ...
    def update_shareholder(self, agent_id: int, firm_id: int, quantity: float) -> None:
        """
        주주 명부를 갱신합니다. (보유량 설정)
        Delegates to ShareholderRegistry (TD-275).
        """
    def update_reference_prices(self, firms: dict[int, IShareholderView]) -> None:
        """
        기업들의 순자산가치를 기반으로 기준 주가를 업데이트합니다.
        
        Args:
            firms: 기업 ID -> Firm 객체 맵
        """
    def get_stock_price(self, firm_id: int) -> float | None:
        """
        특정 기업의 현재 주가를 반환합니다.
        최근 거래가가 있으면 반환, 없으면 기준가를 반환합니다.
        """
    def get_price(self, item_id: str) -> float:
        """
        Returns the current market price for the given stock item (e.g., 'stock_123').
        IMarket Implementation.
        """
    def get_daily_avg_price(self, firm_id: int | None = None) -> float:
        """
        특정 기업의 일일 평균 거래 가격을 반환합니다.
        firm_id가 없으면 전체 평균을 반환합니다.
        """
    def get_daily_volume(self) -> float:
        """
        시장 전체의 일일 거래량을 반환합니다.
        """
    def get_best_bid(self, firm_id: int) -> float | None:
        """특정 기업 주식의 최고 매수호가를 반환합니다."""
    def get_best_ask(self, firm_id: int) -> float | None:
        """특정 기업 주식의 최저 매도호가를 반환합니다."""
    def place_order(self, order: CanonicalOrderDTO, tick: int) -> None:
        """
        주식 주문을 제출합니다.
        """
    def match_orders(self, tick: int) -> list[Transaction]:
        """
        모든 기업의 주식 주문을 매칭하여 거래를 성사시킵니다.
        Delegates to Stateless Matching Engine.
        """
    def clear_expired_orders(self, current_tick: int) -> int:
        """
        만료된 주문을 제거합니다.
        
        Args:
            current_tick: 현재 시뮬레이션 틱
            
        Returns:
            제거된 주문 수
        """
    def reset_daily_stats(self) -> None:
        """일일 통계를 초기화합니다."""
    def get_market_summary(self, firm_id: int) -> dict[str, Any]:
        """특정 기업의 주식 시장 요약 정보를 반환합니다."""
    def clear_orders(self) -> None:
        """
        모든 주문을 초기화합니다.
        다른 시장과의 인터페이스 호환성을 위한 메서드입니다.
        """
    def cancel_orders(self, agent_id: str) -> None:
        """
        Cancels all orders for the specified agent.
        """
    def get_telemetry_snapshot(self) -> list[OrderTelemetrySchema]:
        """Returns Pydantic schemas for UI consumption."""
