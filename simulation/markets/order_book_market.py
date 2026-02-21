from typing import List, Dict, Any, Optional, override, Tuple
import logging
from collections import deque
import math
from dataclasses import dataclass

from simulation.models import Order, Transaction
from simulation.core_markets import Market
from modules.market.api import CanonicalOrderDTO, OrderBookStateDTO, OrderTelemetrySchema
from simulation.markets.matching_engine import OrderBookMatchingEngine

logger = logging.getLogger(__name__)

@dataclass
class MarketOrder:
    """Internal mutable representation of an order in the order book."""
    agent_id: int | str
    side: str
    item_id: str
    quantity: float
    price_pennies: int # SSoT (Integer Pennies)
    price: float       # Legacy/Display (Float)
    original_id: str
    target_agent_id: Optional[int] = None
    brand_info: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dto(cls, dto: CanonicalOrderDTO) -> 'MarketOrder':
        # Ensure price_pennies is available. DTO should enforce this.
        return cls(
            agent_id=dto.agent_id,
            side=dto.side,
            item_id=dto.item_id,
            quantity=dto.quantity,
            price_pennies=dto.price_pennies,
            price=dto.price_limit, # Legacy float
            original_id=dto.id,
            target_agent_id=dto.target_agent_id,
            brand_info=dto.brand_info
        )

    @property
    def order_type(self) -> str:
        return self.side

    def to_dto(self, market_id: str) -> CanonicalOrderDTO:
        """Converts internal MarketOrder to public immutable CanonicalOrderDTO."""
        return CanonicalOrderDTO(
            agent_id=self.agent_id,
            side=self.side,
            item_id=self.item_id,
            quantity=self.quantity,
            price_pennies=self.price_pennies,
            price_limit=self.price,
            market_id=market_id,
            target_agent_id=self.target_agent_id,
            brand_info=self.brand_info
        )


class OrderBookMarket(Market):
    """호가창(Order Book) 기반의 시장을 시뮬레이션하는 클래스.

    매수/매도 주문을 접수하고, 가격 우선 및 시간 우선 원칙에 따라 주문을 매칭하여 거래를 체결합니다.
    """

    def __init__(self, market_id: str, config_module: Any = None, logger: Optional[logging.Logger] = None):
        """OrderBookMarket을 초기화합니다.

        Args:
            market_id (str): 시장의 고유 ID (예: 'goods_market', 'labor_market').
            config_module (Any, optional): 시뮬레이션 설정 모듈.
            logger (logging.Logger, optional): 로깅을 위한 Logger 인스턴스. 기본값은 None.
        """
        super().__init__(market_id=market_id, logger=logger) # Call parent constructor to set self.id and logger
        self.id = market_id
        self.config_module = config_module
        # TD-271: Internal state encapsulated
        self._buy_orders: Dict[str, List[MarketOrder]] = {}
        self._sell_orders: Dict[str, List[MarketOrder]] = {}

        self.daily_avg_price: Dict[str, float] = {}
        self.daily_total_volume: Dict[str, float] = {}
        self.last_traded_prices: Dict[str, float] = {}
        self.last_trade_ticks: Dict[str, int] = {} # Phase 2: Track staleness
        
        # --- GEMINI_ADDITION: Persist signals across ticks ---
        self.cached_best_bid: Dict[str, float] = {}
        self.cached_best_ask: Dict[str, float] = {}
        
        self.last_tick_supply: float = 0.0
        self.last_tick_demand: float = 0.0

        # WO-136: Dynamic Circuit Breakers (Price History)
        # Store last 20 trade prices per item for volatility calculation
        self.price_history: Dict[str, deque] = {}

        # Phase 10: Stateless Matching Engine
        self.matching_engine = OrderBookMatchingEngine()

        self.logger.info(
            f"OrderBookMarket {self.id} initialized.",
            extra={"tick": 0, "market_id": self.id, "tags": ["init", "market"]},
        )

    # --- TD-271: Public Interface Implementation ---

    @property
    def buy_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        """Returns active buy orders as immutable CanonicalOrderDTOs."""
        return {
            item_id: [order.to_dto(self.id) for order in orders]
            for item_id, orders in self._buy_orders.items()
        }

    @property
    def sell_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        """Returns active sell orders as immutable CanonicalOrderDTOs."""
        return {
            item_id: [order.to_dto(self.id) for order in orders]
            for item_id, orders in self._sell_orders.items()
        }

    def _update_price_history(self, item_id: str, price: float):
        """Update the sliding window of price history."""
        window_size = getattr(self.config_module, "PRICE_VOLATILITY_WINDOW_TICKS", 20) if self.config_module else 20

        if item_id not in self.price_history:
            self.price_history[item_id] = deque(maxlen=window_size)
        elif self.price_history[item_id].maxlen != window_size:
            # Resize if config changed
            self.price_history[item_id] = deque(self.price_history[item_id], maxlen=window_size)

        self.price_history[item_id].append(price)

    def get_dynamic_price_bounds(self, item_id: str) -> Tuple[float, float]:
        """
        Calculate adaptive price bounds based on volatility.
        Formula: Bounds = Mean * (1 ± (Base_Limit * Volatility_Adj))
        Volatility_Adj = 1 + (StdDev / Mean)
        """
        # Phase 1: Relax circuit breakers for price discovery
        min_history_len = getattr(self.config_module, "CIRCUIT_BREAKER_MIN_HISTORY", 7) if self.config_module else 7

        if item_id not in self.price_history or len(self.price_history[item_id]) < min_history_len:
            self.logger.debug(f"History-Free Discovery: Widening bounds for {item_id}.")
            return 0.0, float('inf') # No bounds yet

        history = list(self.price_history[item_id])
        mean_price = sum(history) / len(history)

        if mean_price <= 0:
            return 0.0, float('inf')

        variance = sum((p - mean_price) ** 2 for p in history) / len(history)
        std_dev = math.sqrt(variance)

        volatility_adj = 1.0 + (std_dev / mean_price)
        # WO-136: Use config for base limit
        base_limit = getattr(self.config_module, "MARKET_CIRCUIT_BREAKER_BASE_LIMIT", 0.15)

        lower_bound = mean_price * (1.0 - (base_limit * volatility_adj))
        upper_bound = mean_price * (1.0 + (base_limit * volatility_adj))

        return max(0.0, lower_bound), upper_bound


    def clear_orders(self) -> None:
        """현재 틱의 모든 주문을 초기화합니다. 초기화 전 Best Bid/Ask를 캐싱합니다."""
        # WO-053: Capture stats before clearing
        self.last_tick_supply = self.get_total_supply()
        self.last_tick_demand = self.get_total_demand()

        # Cache best prices for signal persistence
        for item_id in set(list(self._buy_orders.keys()) + list(self._sell_orders.keys())):
            bid = self.get_best_bid(item_id)
            if bid is not None: self.cached_best_bid[item_id] = bid
            
            ask = self.get_best_ask(item_id)
            if ask is not None: self.cached_best_ask[item_id] = ask

        self._buy_orders.clear()
        self._sell_orders.clear()
        self.daily_avg_price.clear()
        self.daily_total_volume.clear()
        self.logger.debug(
            f"Market {self.id} orders cleared for new tick.",
            extra={"market_id": self.id, "tags": ["market_clear"]},
        )

    def cancel_orders(self, agent_id: str) -> None:
        """
        Cancels all orders for the specified agent.
        Iterates through buy and sell orders and removes any belonging to the agent.
        """
        removed_count = 0

        # Iterate over buy orders
        for item_id, orders in self._buy_orders.items():
            original_len = len(orders)
            self._buy_orders[item_id] = [o for o in orders if o.agent_id != agent_id]
            removed_count += original_len - len(self._buy_orders[item_id])

        # Iterate over sell orders
        for item_id, orders in self._sell_orders.items():
            original_len = len(orders)
            self._sell_orders[item_id] = [o for o in orders if o.agent_id != agent_id]
            removed_count += original_len - len(self._sell_orders[item_id])

        if removed_count > 0:
            self.logger.info(
                f"CANCEL_ORDERS | Removed {removed_count} orders for agent {agent_id}",
                extra={"market_id": self.id, "agent_id": agent_id, "removed_count": removed_count}
            )

    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int):
        """시장에 주문을 제출합니다. 매칭은 별도의 메서드로 처리됩니다.
        WO-136: Checks dynamic circuit breakers before accepting.

        Args:
            order_dto (CanonicalOrderDTO): 제출할 주문 객체.
            current_time (int): 현재 시뮬레이션 틱 (시간) 입니다.
        """
        # WO-136: Circuit Breaker Check
        min_price, max_price = self.get_dynamic_price_bounds(order_dto.item_id)
        if order_dto.price_limit < min_price or order_dto.price_limit > max_price:
            # Check if bounds are active (max_price < inf)
            if max_price < float('inf'):
                self.logger.warning(
                    f"CIRCUIT_BREAKER | Order rejected. Price {order_dto.price_limit:.2f} out of bounds [{min_price:.2f}, {max_price:.2f}]",
                    extra={
                        "tick": current_time,
                        "market_id": self.id,
                        "agent_id": order_dto.agent_id,
                        "item_id": order_dto.item_id,
                        "price": order_dto.price_limit,
                        "bounds": (min_price, max_price)
                    }
                )
                return # Reject order

        # Convert to mutable MarketOrder
        order = MarketOrder.from_dto(order_dto)

        log_extra = {
            "tick": current_time,
            "market_id": self.id,
            "agent_id": order.agent_id,
            "item_id": order.item_id,
            "side": order.side,
            "price": order.price,
            "quantity": order.quantity,
        }
        self.logger.debug(
            f"Placing order: {order.side} {order.quantity} of {order.item_id} at {order.price} by {order.agent_id}",
            extra=log_extra,
        )
        self._add_order(order, log_extra)

    def match_orders(self, current_time: int) -> List[Transaction]:
        """
        현재 틱의 모든 주문을 매칭하고 거래를 실행합니다.
        각 아이템별로 주문 매칭을 수행합니다.
        """
        all_transactions: List[Transaction] = []

        # Get all unique item_ids from both buy and sell orders
        all_item_ids = set(self._buy_orders.keys()) | set(self._sell_orders.keys())

        if not all_item_ids:
            self.logger.info(
                f"No items to match in market {self.id} at tick {current_time}",
                extra={
                    "tick": current_time,
                    "market_id": self.id,
                    "tags": ["market_match"],
                },
            )
            return all_transactions

        self.logger.info(
            f"Starting order matching for items: {list(all_item_ids)}",
            extra={
                "tick": current_time,
                "market_id": self.id,
                "tags": ["market_match"],
            },
        )

        # 1. Prepare State DTO
        buy_orders_dto = {
            item_id: [order.to_dto(self.id) for order in orders]
            for item_id, orders in self._buy_orders.items()
        }
        sell_orders_dto = {
            item_id: [order.to_dto(self.id) for order in orders]
            for item_id, orders in self._sell_orders.items()
        }

        state = OrderBookStateDTO(
            buy_orders=buy_orders_dto,
            sell_orders=sell_orders_dto,
            market_id=self.id
        )

        # 2. Execute Matching via Engine
        result = self.matching_engine.match(state, current_time)

        # 3. Apply Results
        all_transactions = result.transactions
        self.matched_transactions.extend(all_transactions)

        # Update Order Books (Replace with unfilled)
        self._buy_orders = {
            item_id: [MarketOrder.from_dto(dto) for dto in dtos]
            for item_id, dtos in result.unfilled_buy_orders.items()
        }
        self._sell_orders = {
            item_id: [MarketOrder.from_dto(dto) for dto in dtos]
            for item_id, dtos in result.unfilled_sell_orders.items()
        }

        # Update Market Stats
        for item_id, price in result.market_stats.get("last_traded_prices", {}).items():
            self.last_traded_prices[item_id] = price
            self._update_price_history(item_id, price)

        for item_id, tick in result.market_stats.get("last_trade_ticks", {}).items():
            self.last_trade_ticks[item_id] = tick

        for item_id, volume in result.market_stats.get("daily_total_volume", {}).items():
             self.daily_total_volume[item_id] = self.daily_total_volume.get(item_id, 0.0) + volume

        return all_transactions

    def _add_order(self, order: MarketOrder, log_extra: Dict[str, Any]):
        # Determine which order book to use based on side
        if order.side == "BUY":
            target_order_book = self._buy_orders
        elif order.side == "SELL":
            target_order_book = self._sell_orders
        else:
            self.logger.warning(
                f"Unknown side for _add_order: {order.side}",
                extra=log_extra,
            )
            return

        if order.item_id not in target_order_book:
            target_order_book[order.item_id] = []
        target_order_book[order.item_id].append(order)
        # Sort orders: BUY by price_pennies (desc), SELL by price_pennies (asc)
        if order.side == "BUY":
            target_order_book[order.item_id].sort(key=lambda o: o.price_pennies, reverse=True)
        else:
            target_order_book[order.item_id].sort(key=lambda o: o.price_pennies)

    def get_best_ask(self, item_id: str) -> float | None:
        """주어진 아이템의 최저 판매 가격(best ask)을 반환합니다."""
        if item_id in self._sell_orders and self._sell_orders[item_id]:
            return self._sell_orders[item_id][0].price
        return self.cached_best_ask.get(item_id)

    def get_best_bid(self, item_id: str) -> float | None:
        """주어진 아이템의 최고 구매 가격(best bid)을 반환합니다."""
        if item_id in self._buy_orders and self._buy_orders[item_id]:
            return self._buy_orders[item_id][0].price
        return self.cached_best_bid.get(item_id)

    def get_last_traded_price(self, item_id: str) -> float | None:
        """주어진 아이템의 마지막 체결 가격을 반환합니다."""
        return self.last_traded_prices.get(item_id)

    def get_price(self, item_id: str) -> float:
        """
        Returns the current market price for the given item (IMarket Implementation).
        Returns last traded price or 0.0 if not available.
        """
        price = self.last_traded_prices.get(item_id)
        return price if price is not None else 0.0

    def get_last_trade_tick(self, item_id: str) -> int | None:
        """Returns the tick of the last trade for the item."""
        return self.last_trade_ticks.get(item_id)

    def get_spread(self, item_id: str) -> float | None:
        """주어진 아이템의 매도-매수 스프레드를 반환합니다."""
        best_ask = self.get_best_ask(item_id)
        best_bid = self.get_best_bid(item_id)
        if best_ask is None or best_bid is None:
            return None
        return best_ask - best_bid

    def get_market_depth(self, item_id: str) -> Dict[str, int]:
        """주어진 아이템의 매수/매도 주문 건수를 반환합니다."""
        return {
            "buy_orders": len(self._buy_orders.get(item_id, [])),
            "sell_orders": len(self._sell_orders.get(item_id, [])),
        }

    def get_order_book_status(self, item_id: str) -> Dict[str, Any]:
        """주어진 아이템의 현재 호가창 상태를 반환합니다."""
        return {
            "buy_orders": [
                {"agent_id": o.agent_id, "quantity": o.quantity, "price": o.price}
                for o in self._buy_orders.get(item_id, [])
            ],
            "sell_orders": [
                {"agent_id": o.agent_id, "quantity": o.quantity, "price": o.price}
                for o in self._sell_orders.get(item_id, [])
            ],
        }

    def get_all_bids(self, item_id: str) -> List[MarketOrder]:
        """주어진 아이템의 모든 매수 주문을 반환합니다."""
        return self._buy_orders.get(item_id, [])

    def get_all_asks(self, item_id: str) -> List[MarketOrder]:
        """주어진 아이템의 모든 매도 주문을 반환합니다."""
        return self._sell_orders.get(item_id, [])

    def get_total_demand(self) -> float:
        """시장의 모든 매수 주문 총량을 반환합니다."""
        return sum(
            order.quantity for orders in self._buy_orders.values() for order in orders
        )

    def get_total_supply(self) -> float:
        """시장의 모든 매도 주문 총량을 반환합니다."""
        return sum(
            order.quantity for orders in self._sell_orders.values() for order in orders
        )

    def get_daily_avg_price(self) -> float:
        """
        해당 시장의 일일 평균 거래 가격을 반환합니다.
        매칭된 거래가 없으면 0.0을 반환합니다.
        """
        if not self.matched_transactions:
            return 0.0
        total_price = sum(tx.price * tx.quantity for tx in self.matched_transactions)
        total_quantity = sum(tx.quantity for tx in self.matched_transactions)
        return total_price / total_quantity if total_quantity > 0 else 0.0

    def get_daily_volume(self) -> float:
        """
        해당 시장의 일일 거래량을 반환합니다.
        """
        return sum(tx.quantity for tx in self.matched_transactions)

    def get_telemetry_snapshot(self) -> List[OrderTelemetrySchema]:
        """Returns Pydantic schemas for UI consumption."""
        snapshot = []
        for item_id, orders in self._buy_orders.items():
            for order in orders:
                dto = order.to_dto(self.id)
                snapshot.append(OrderTelemetrySchema.from_canonical(dto))
        for item_id, orders in self._sell_orders.items():
            for order in orders:
                dto = order.to_dto(self.id)
                snapshot.append(OrderTelemetrySchema.from_canonical(dto))
        return snapshot
