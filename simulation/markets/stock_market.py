"""
주식 시장 (Stock Market)

가계와 기업 간 주식 거래를 중개하는 시장 클래스입니다.
기존 OrderBookMarket과 유사한 가격-시간 우선 원칙을 적용합니다.
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING, Union
import logging
from collections import defaultdict
from dataclasses import dataclass, replace
from simulation.models import Transaction, Order
from simulation.core_markets import Market
from modules.market.api import CanonicalOrderDTO, StockMarketStateDTO, StockIDHelper, OrderTelemetrySchema, IIndexCircuitBreaker
from modules.finance.api import IShareholderRegistry, IShareholderView
from simulation.markets.matching_engine import StockMatchingEngine
logger = logging.getLogger(__name__)

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

    def __init__(self, config_module: Any, shareholder_registry: IShareholderRegistry, logger: Optional[logging.Logger]=None, index_circuit_breaker: Optional[IIndexCircuitBreaker]=None):
        self.id = 'stock_market'
        self.config_module = config_module
        self.logger = logger or logging.getLogger(__name__)
        self.shareholder_registry = shareholder_registry
        self.index_circuit_breaker = index_circuit_breaker
        self.matched_transactions: List[Transaction] = []
        self.buy_orders: Dict[int, List[ManagedOrder]] = defaultdict(list)
        self.sell_orders: Dict[int, List[ManagedOrder]] = defaultdict(list)
        self.last_prices: Dict[int, float] = {}
        self.reference_prices: Dict[int, float] = {}
        self.daily_volumes: Dict[int, float] = {}
        self.daily_high: Dict[int, float] = {}
        self.daily_low: Dict[int, float] = {}
        self.matching_engine = StockMatchingEngine()

    def update_shareholder(self, agent_id: int, firm_id: int, quantity: float) -> None:
        """
        주주 명부를 갱신합니다. (보유량 설정)
        Delegates to ShareholderRegistry (TD-275).
        """
        self.shareholder_registry.register_shares(firm_id, agent_id, quantity)

    def update_reference_prices(self, firms: Dict[int, IShareholderView]) -> None:
        """
        기업들의 순자산가치를 기반으로 기준 주가를 업데이트합니다.
        
        Args:
            firms: 기업 ID -> Firm 객체 맵
        """
        multiplier = getattr(self.config_module, 'STOCK_BOOK_VALUE_MULTIPLIER', 1.0)
        for firm_id, firm in firms.items():
            if not getattr(firm, 'is_active', True):
                continue
            book_value = self._calculate_book_value_per_share(firm)
            self.reference_prices[firm_id] = max(0.01, book_value * multiplier)

    def _calculate_book_value_per_share(self, firm: IShareholderView) -> float:
        """기업의 주당 순자산가치를 계산합니다."""
        return firm.get_book_value_per_share()

    def get_stock_price(self, firm_id: int) -> Optional[float]:
        """
        특정 기업의 현재 주가를 반환합니다.
        최근 거래가가 있으면 반환, 없으면 기준가를 반환합니다.
        """
        if firm_id in self.last_prices:
            return self.last_prices[firm_id]
        return self.reference_prices.get(firm_id)

    def get_price(self, item_id: str) -> float:
        """
        Returns the current market price for the given stock item (e.g., 'stock_123').
        IMarket Implementation.
        """
        try:
            firm_id = StockIDHelper.parse_firm_id(item_id)
            price = self.get_stock_price(firm_id)
            return price if price is not None else 0.0
        except ValueError:
            # Try parsing as raw int for legacy compatibility if strict parsing fails
            try:
                firm_id = int(item_id)
                price = self.get_stock_price(firm_id)
                return price if price is not None else 0.0
            except ValueError:
                self.logger.warning(f"Invalid item_id for get_price: {item_id}")
                return 0.0

    def get_daily_avg_price(self, firm_id: Optional[int]=None) -> float:
        """
        특정 기업의 일일 평균 거래 가격을 반환합니다.
        firm_id가 없으면 전체 평균을 반환합니다.
        """
        if firm_id is not None:
            return self.get_stock_price(firm_id) or 0.0
        if not self.last_prices:
            return 0.0
        return sum(self.last_prices.values()) / len(self.last_prices)

    def get_daily_volume(self) -> float:
        """
        시장 전체의 일일 거래량을 반환합니다.
        """
        return sum(self.daily_volumes.values())

    def get_best_bid(self, firm_id: int) -> Optional[float]:
        """특정 기업 주식의 최고 매수호가를 반환합니다."""
        orders = self.buy_orders.get(firm_id, [])
        if not orders:
            return None
        return max((managed.order.price_limit for managed in orders))

    def get_best_ask(self, firm_id: int) -> Optional[float]:
        """특정 기업 주식의 최저 매도호가를 반환합니다."""
        orders = self.sell_orders.get(firm_id, [])
        if not orders:
            return None
        return min((managed.order.price_limit for managed in orders))

    def place_order(self, order: CanonicalOrderDTO, tick: int) -> None:
        """
        주식 주문을 제출합니다.
        """
        if not isinstance(order, CanonicalOrderDTO):
            self.logger.error(f'Invalid order type passed to StockMarket: {type(order)}. Expected CanonicalOrderDTO.')
            return
        try:
            firm_id = StockIDHelper.parse_firm_id(order.item_id)
        except ValueError:
            self.logger.error(f"Invalid item_id format for stock order: {order.item_id}. Expected 'stock_<firm_id>'")
            return
        limit_rate = getattr(self.config_module, 'STOCK_PRICE_LIMIT_RATE', 0.1)
        ref_price = self.reference_prices.get(firm_id, order.price_limit)
        min_price = ref_price * (1 - limit_rate)
        max_price = ref_price * (1 + limit_rate)
        final_order = order
        if order.price_limit < min_price or order.price_limit > max_price:
            self.logger.warning(f'Stock order price {order.price_limit:.2f} out of limit range [{min_price:.2f}, {max_price:.2f}] for firm {firm_id}', extra={'tick': tick, 'agent_id': order.agent_id, 'firm_id': firm_id})
            clamped_price = max(min_price, min(max_price, order.price_limit))
            clamped_pennies = int(clamped_price * 100)
            final_order = replace(order, price_limit=clamped_price, price_pennies=clamped_pennies)
        managed_order = ManagedOrder(order=final_order, remaining_quantity=final_order.quantity, created_tick=tick)
        if final_order.side == 'BUY':
            self.buy_orders[firm_id].append(managed_order)
            self.buy_orders[firm_id].sort(key=lambda m: -m.order.price_limit)
        elif final_order.side == 'SELL':
            self.sell_orders[firm_id].append(managed_order)
            self.sell_orders[firm_id].sort(key=lambda m: m.order.price_limit)
        else:
            self.logger.warning(f'Unknown stock order side: {final_order.side}', extra={'tick': tick, 'agent_id': final_order.agent_id})
            return
        self.logger.info(f'Stock {final_order.side} order placed: {final_order.quantity:.1f} shares of firm {firm_id} at {final_order.price_limit:.2f}', extra={'tick': tick, 'agent_id': final_order.agent_id, 'firm_id': firm_id, 'order_type': final_order.side, 'quantity': final_order.quantity, 'price': final_order.price_limit, 'tags': ['stock', 'order']})

    def match_orders(self, tick: int) -> List[Transaction]:
        """
        모든 기업의 주식 주문을 매칭하여 거래를 성사시킵니다.
        Delegates to Stateless Matching Engine.
        """
        # WO-IMPL-INDEX-BREAKER: Check Market Health
        # We only READ the state. The orchestrator updates it centrally.
        if self.index_circuit_breaker and self.index_circuit_breaker.is_active():
            self.logger.warning(
                f"MARKET_HALT | StockMarket halted by IndexCircuitBreaker",
                extra={'tick': tick, 'market_id': self.id}
            )
            return []

        def to_dto_with_metadata(managed: ManagedOrder) -> CanonicalOrderDTO:
            dto = replace(managed.order, quantity=managed.remaining_quantity)
            new_metadata = dto.metadata.copy() if dto.metadata else {}
            new_metadata['created_tick'] = managed.created_tick
            return replace(dto, metadata=new_metadata)
        buy_orders_dto = {firm_id: [to_dto_with_metadata(managed) for managed in orders] for firm_id, orders in self.buy_orders.items()}
        sell_orders_dto = {firm_id: [to_dto_with_metadata(managed) for managed in orders] for firm_id, orders in self.sell_orders.items()}
        state = StockMarketStateDTO(buy_orders=buy_orders_dto, sell_orders=sell_orders_dto, market_id=self.id)
        result = self.matching_engine.match(state, tick)
        for firm_id_str, price in result.market_stats.get('last_prices', {}).items():
            firm_id = int(firm_id_str)
            self.last_prices[firm_id] = price
        for firm_id_str, volume in result.market_stats.get('daily_volumes', {}).items():
            firm_id = int(firm_id_str)
            self.daily_volumes[firm_id] = self.daily_volumes.get(firm_id, 0.0) + volume
        for firm_id_str, high in result.market_stats.get('daily_high', {}).items():
            firm_id = int(firm_id_str)
            if firm_id not in self.daily_high or high > self.daily_high[firm_id]:
                self.daily_high[firm_id] = high
        for firm_id_str, low in result.market_stats.get('daily_low', {}).items():
            firm_id = int(firm_id_str)
            if firm_id not in self.daily_low or low < self.daily_low[firm_id]:
                self.daily_low[firm_id] = low

        def from_dto(dto: CanonicalOrderDTO) -> ManagedOrder:
            created_tick = dto.metadata.get('created_tick', tick) if dto.metadata else tick
            return ManagedOrder(order=dto, remaining_quantity=dto.quantity, created_tick=created_tick)
        self.buy_orders = defaultdict(list)
        for firm_id_str, dtos in result.unfilled_buy_orders.items():
            firm_id = int(firm_id_str)
            self.buy_orders[firm_id] = [from_dto(dto) for dto in dtos]
        self.sell_orders = defaultdict(list)
        for firm_id_str, dtos in result.unfilled_sell_orders.items():
            firm_id = int(firm_id_str)
            self.sell_orders[firm_id] = [from_dto(dto) for dto in dtos]
        return result.transactions

    def clear_expired_orders(self, current_tick: int) -> int:
        """
        만료된 주문을 제거합니다.
        
        Args:
            current_tick: 현재 시뮬레이션 틱
            
        Returns:
            제거된 주문 수
        """
        expiry_ticks = getattr(self.config_module, 'STOCK_ORDER_EXPIRY_TICKS', 5)
        removed_count = 0
        for firm_id in list(self.buy_orders.keys()):
            original_count = len(self.buy_orders[firm_id])
            self.buy_orders[firm_id] = [managed for managed in self.buy_orders[firm_id] if current_tick - managed.created_tick < expiry_ticks]
            removed = original_count - len(self.buy_orders[firm_id])
            removed_count += removed
        for firm_id in list(self.sell_orders.keys()):
            original_count = len(self.sell_orders[firm_id])
            self.sell_orders[firm_id] = [managed for managed in self.sell_orders[firm_id] if current_tick - managed.created_tick < expiry_ticks]
            removed = original_count - len(self.sell_orders[firm_id])
            removed_count += removed
        if removed_count > 0:
            self.logger.debug(f'Cleared {removed_count} expired stock orders', extra={'tick': current_tick, 'tags': ['stock', 'cleanup']})
        return removed_count

    def reset_daily_stats(self) -> None:
        """일일 통계를 초기화합니다."""
        self.daily_volumes.clear()
        self.daily_high.clear()
        self.daily_low.clear()

    def get_market_summary(self, firm_id: int) -> Dict[str, Any]:
        """특정 기업의 주식 시장 요약 정보를 반환합니다."""
        return {'firm_id': firm_id, 'last_price': self.last_prices.get(firm_id), 'reference_price': self.reference_prices.get(firm_id), 'best_bid': self.get_best_bid(firm_id), 'best_ask': self.get_best_ask(firm_id), 'daily_volume': self.daily_volumes.get(firm_id, 0), 'daily_high': self.daily_high.get(firm_id), 'daily_low': self.daily_low.get(firm_id), 'buy_order_count': len(self.buy_orders.get(firm_id, [])), 'sell_order_count': len(self.sell_orders.get(firm_id, []))}

    def clear_orders(self) -> None:
        """
        모든 주문을 초기화합니다.
        다른 시장과의 인터페이스 호환성을 위한 메서드입니다.
        """
        self.buy_orders.clear()
        self.sell_orders.clear()
        self.reset_daily_stats()

    def cancel_orders(self, agent_id: str) -> None:
        """
        Cancels all orders for the specified agent.
        """
        removed_count = 0

        # Iterate over buy orders
        for firm_id, orders in self.buy_orders.items():
            original_len = len(orders)
            # ManagedOrder.order is CanonicalOrderDTO
            self.buy_orders[firm_id] = [
                m for m in orders
                if str(m.order.agent_id) != str(agent_id) and m.order.agent_id != agent_id
            ]
            removed_count += original_len - len(self.buy_orders[firm_id])

        # Iterate over sell orders
        for firm_id, orders in self.sell_orders.items():
            original_len = len(orders)
            self.sell_orders[firm_id] = [
                m for m in orders
                if str(m.order.agent_id) != str(agent_id) and m.order.agent_id != agent_id
            ]
            removed_count += original_len - len(self.sell_orders[firm_id])

        if removed_count > 0:
            self.logger.info(
                f"CANCEL_ORDERS | Removed {removed_count} stock orders for agent {agent_id}",
                extra={"market_id": self.id, "agent_id": agent_id, "removed_count": removed_count}
            )

    def get_telemetry_snapshot(self) -> List[OrderTelemetrySchema]:
        """Returns Pydantic schemas for UI consumption."""
        snapshot = []
        for firm_id, orders in self.buy_orders.items():
            for managed in orders:
                # ManagedOrder.order is CanonicalOrderDTO
                snapshot.append(OrderTelemetrySchema.from_canonical(managed.order))
        for firm_id, orders in self.sell_orders.items():
            for managed in orders:
                snapshot.append(OrderTelemetrySchema.from_canonical(managed.order))
        return snapshot