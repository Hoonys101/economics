from typing import List, Dict, Any, Optional, override, Tuple
import logging
from collections import deque
import math

from simulation.models import Order, Transaction
from simulation.core_markets import Market

logger = logging.getLogger(__name__)


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
        self.buy_orders: Dict[str, List[Order]] = {}
        self.sell_orders: Dict[str, List[Order]] = {}
        self.daily_avg_price: Dict[str, float] = {}
        self.daily_total_volume: Dict[str, float] = {}
        self.last_traded_prices: Dict[str, float] = {}
        
        # --- GEMINI_ADDITION: Persist signals across ticks ---
        self.cached_best_bid: Dict[str, float] = {}
        self.cached_best_ask: Dict[str, float] = {}
        
        self.last_tick_supply: float = 0.0
        self.last_tick_demand: float = 0.0

        # WO-136: Dynamic Circuit Breakers (Price History)
        # Store last 20 trade prices per item for volatility calculation
        self.price_history: Dict[str, deque] = {}

        self.logger.info(
            f"OrderBookMarket {self.id} initialized.",
            extra={"tick": 0, "market_id": self.id, "tags": ["init", "market"]},
        )

    def _update_price_history(self, item_id: str, price: float):
        """Update the sliding window of price history."""
        if item_id not in self.price_history:
            self.price_history[item_id] = deque(maxlen=20)
        self.price_history[item_id].append(price)

    def get_dynamic_price_bounds(self, item_id: str) -> Tuple[float, float]:
        """
        Calculate adaptive price bounds based on volatility.
        Formula: Bounds = Mean * (1 ± (Base_Limit * Volatility_Adj))
        Volatility_Adj = 1 + (StdDev / Mean)
        """
        if item_id not in self.price_history or len(self.price_history[item_id]) < 2:
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
        for item_id in set(list(self.buy_orders.keys()) + list(self.sell_orders.keys())):
            bid = self.get_best_bid(item_id)
            if bid is not None: self.cached_best_bid[item_id] = bid
            
            ask = self.get_best_ask(item_id)
            if ask is not None: self.cached_best_ask[item_id] = ask

        self.buy_orders.clear()
        self.sell_orders.clear()
        self.daily_avg_price.clear()
        self.daily_total_volume.clear()
        self.logger.debug(
            f"Market {self.id} orders cleared for new tick.",
            extra={"market_id": self.id, "tags": ["market_clear"]},
        )

    def place_order(self, order: Order, current_time: int):
        """시장에 주문을 제출합니다. 매칭은 별도의 메서드로 처리됩니다.
        WO-136: Checks dynamic circuit breakers before accepting.

        Args:
            order (Order): 제출할 주문 객체.
            current_time (int): 현재 시뮬레이션 틱 (시간) 입니다.
        """
        # WO-136: Circuit Breaker Check
        min_price, max_price = self.get_dynamic_price_bounds(order.item_id)
        if order.price < min_price or order.price > max_price:
            # Check if bounds are active (max_price < inf)
            if max_price < float('inf'):
                self.logger.warning(
                    f"CIRCUIT_BREAKER | Order rejected. Price {order.price:.2f} out of bounds [{min_price:.2f}, {max_price:.2f}]",
                    extra={
                        "tick": current_time,
                        "market_id": self.id,
                        "agent_id": order.agent_id,
                        "item_id": order.item_id,
                        "price": order.price,
                        "bounds": (min_price, max_price)
                    }
                )
                return # Reject order

        log_extra = {
            "tick": current_time,
            "market_id": self.id,
            "agent_id": order.agent_id,
            "item_id": order.item_id,
            "order_type": order.order_type,
            "price": order.price,
            "quantity": order.quantity,
        }
        self.logger.debug(
            f"Placing order: {order.order_type} {order.quantity} of {order.item_id} at {order.price} by {order.agent_id}",
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
        all_item_ids = set(self.buy_orders.keys()) | set(self.sell_orders.keys())

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

        for item_id in all_item_ids:
            item_transactions = self._match_orders_for_item(item_id, current_time)
            all_transactions.extend(item_transactions)
            self.matched_transactions.extend(item_transactions)

        return all_transactions

    def _add_order(self, order: Order, log_extra: Dict[str, Any]):
        # Determine which order book to use based on order type
        if order.order_type == "BUY":
            target_order_book = self.buy_orders
        elif order.order_type == "SELL":
            target_order_book = self.sell_orders
        else:
            self.logger.warning(
                f"Unknown order type for _add_order: {order.order_type}",
                extra=log_extra,
            )
            return

        if order.item_id not in target_order_book:
            target_order_book[order.item_id] = []
        target_order_book[order.item_id].append(order)
        # Sort orders: BUY by price (desc), SELL by price (asc)
        if order.order_type == "BUY":
            target_order_book[order.item_id].sort(key=lambda o: o.price, reverse=True)
        else:
            target_order_book[order.item_id].sort(key=lambda o: o.price)

    def _match_orders_for_item(
        self, item_id: str, current_tick: int
    ) -> List[Transaction]:
        """주어진 아이템에 대해 매수/매도 주문을 매칭하고 거래를 체결합니다.
        Phase 6: Targeted Orders (Brand Economy) are processed first.
        """
        transactions = []
        log_extra = {
            "tick": current_tick,
            "market_id": self.id,
            "item_id": item_id,
        }

        buy_orders_list = self.buy_orders.get(item_id, [])
        sell_orders_list = self.sell_orders.get(item_id, [])

        if not buy_orders_list or not sell_orders_list:
            return transactions

        # --- Phase 6: Targeted Matching ---
        # 1. Separate targeted vs general buys
        targeted_buys = []
        general_buys = []
        for order in buy_orders_list:
            if order.target_agent_id is not None:
                targeted_buys.append(order)
            else:
                general_buys.append(order)
        
        # 2. Process Targeted Buys
        # Targeted buys ignore price sorting? No, usually handled FIFO or by price within target.
        # But here we just iterate list. Detailed sorting within target isn't critical for V1.
        
        # Create a map of Sell orders for fast lookup by AgentID
        # Dictionary of AgentID -> List[Order]
        sell_map: Dict[int, List[Order]] = {}
        for s_order in sell_orders_list:
             if s_order.agent_id not in sell_map:
                 sell_map[s_order.agent_id] = []
             sell_map[s_order.agent_id].append(s_order)
             
        remaining_targeted_buys = []
        
        for b_order in targeted_buys:
             target_id = b_order.target_agent_id
             # Check if target seller has stock
             target_asks = sell_map.get(target_id)
             
             if target_asks and target_asks[0].quantity > 0:
                 s_order = target_asks[0] # Pick best price ask from this seller (assuming sorted)
                 
                 # Price Check: Does buyer accept seller's price?
                 if b_order.price >= s_order.price:
                     trade_price = s_order.price # Brand Loyalty -> Pay Ask Price
                     trade_quantity = min(b_order.quantity, s_order.quantity)
                     
                     transaction = Transaction(
                         item_id=item_id,
                         quantity=trade_quantity,
                         price=trade_price,
                         buyer_id=b_order.agent_id,
                         seller_id=s_order.agent_id,
                         market_id=self.id,
                         transaction_type="labor" if "labor" in self.id else ("housing" if "housing" in self.id else "goods"),
                         time=current_tick,
                         quality=s_order.brand_info.get("quality", 1.0) if s_order.brand_info else 1.0
                     )
                     self.last_traded_prices[item_id] = trade_price
                     # WO-136: Update Price History
                     self._update_price_history(item_id, trade_price)
                     transactions.append(transaction)
                     
                     self.logger.info(
                         f"MATCHED_TARGETED | {trade_quantity:.2f} of {item_id} at {trade_price:.2f}. "
                         f"Buyer {b_order.agent_id} -> Seller {s_order.agent_id} (Targeted)",
                         extra={**log_extra, "buyer_id":b_order.agent_id, "seller_id":s_order.agent_id, "match_type": "targeted"}
                     )
                     
                     b_order.quantity -= trade_quantity
                     s_order.quantity -= trade_quantity
                     
                     if s_order.quantity <= 0.001:
                         target_asks.pop(0) # Remove exhausted ask
                         
                 else:
                     # Price mismatch (Buyer willing to pay X, Seller wants Y, X < Y)
                     # Transaction fails. Buyer waits or enters general pool?
                     # Spec says "Strict Targeting -> Fails".
                     pass
             else:
                 # Target sold out or not present
                 pass
             
             if b_order.quantity > 0.001:
                 # Failed to fill completely
                 remaining_targeted_buys.append(b_order)

        # Fallback: Add remaining targeted buys to general pool
        # This fixes "Starvation by Brand Loyalty" where buyers wouldn't buy from others if target failed.
        if remaining_targeted_buys:
            general_buys.extend(remaining_targeted_buys)
            # Re-sort general buys by price desc to maintain priority
            general_buys.sort(key=lambda o: o.price, reverse=True)

        # Re-flatten sell map to list for general matching
        remaining_sells = []
        for s_list in sell_map.values():
            remaining_sells.extend(s_list)
        # Sort by price (asc) for general matching
        remaining_sells.sort(key=lambda o: o.price)
        
        # General Matching Loop
        idx_b = 0
        idx_s = 0
        
        while idx_b < len(general_buys) and idx_s < len(remaining_sells):
            b_order = general_buys[idx_b]
            s_order = remaining_sells[idx_s]
            
            if b_order.quantity <= 0.001:
                idx_b += 1
                continue
            if s_order.quantity <= 0.001:
                idx_s += 1
                continue
                
            if b_order.price >= s_order.price:
                # Labor Market Logic
                if self.id == "labor" or self.id == "research_labor":
                    trade_price = b_order.price
                else:
                    trade_price = (b_order.price + s_order.price) / 2
                
                trade_quantity = min(b_order.quantity, s_order.quantity)
                
                transaction = Transaction(
                    item_id=item_id,
                    quantity=trade_quantity,
                    price=trade_price,
                    buyer_id=b_order.agent_id,
                    seller_id=s_order.agent_id,
                    market_id=self.id,
                    transaction_type="labor" if "labor" in self.id else ("housing" if "housing" in self.id else "goods"),
                    time=current_tick,
                    quality=s_order.brand_info.get("quality", 1.0) if s_order.brand_info else 1.0
                )
                self.last_traded_prices[item_id] = trade_price
                # WO-136: Update Price History
                self._update_price_history(item_id, trade_price)
                transactions.append(transaction)
                
                self.logger.info(
                    f"MATCHED_GENERAL | {trade_quantity:.2f} of {item_id} at {trade_price:.2f}. "
                    f"Buyer {b_order.agent_id} -> Seller {s_order.agent_id}",
                    extra={**log_extra, "buyer_id":b_order.agent_id, "seller_id":s_order.agent_id, "match_type": "general"}
                )
                
                b_order.quantity -= trade_quantity
                s_order.quantity -= trade_quantity
            else:
                 # Prices don't cross anymore (lists are sorted)
                 break
        
        # Re-save lists to cleanup empty orders
        # (Actually the main lists hold references, but we need to ensure self.buy_orders refers to the updated state)
        # Simplification: Just keep non-empty orders in the main list.
        # We need to combine remaining_targeted and remaining_general
        
        new_buy_list = [o for o in (remaining_targeted_buys + general_buys) if o.quantity > 0.001]
        new_buy_list.sort(key=lambda o: o.price, reverse=True) # Maintain sorted invariant
        
        new_sell_list = [o for o in remaining_sells if o.quantity > 0.001]
        new_sell_list.sort(key=lambda o: o.price)
        
        self.buy_orders[item_id] = new_buy_list
        self.sell_orders[item_id] = new_sell_list

        return transactions

    def get_best_ask(self, item_id: str) -> float | None:
        """주어진 아이템의 최저 판매 가격(best ask)을 반환합니다."""
        if item_id in self.sell_orders and self.sell_orders[item_id]:
            return self.sell_orders[item_id][0].price
        return self.cached_best_ask.get(item_id)

    def get_best_bid(self, item_id: str) -> float | None:
        """주어진 아이템의 최고 구매 가격(best bid)을 반환합니다."""
        if item_id in self.buy_orders and self.buy_orders[item_id]:
            return self.buy_orders[item_id][0].price
        return self.cached_best_bid.get(item_id)

    def get_last_traded_price(self, item_id: str) -> float | None:
        """주어진 아이템의 마지막 체결 가격을 반환합니다."""
        return self.last_traded_prices.get(item_id)

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
            "buy_orders": len(self.buy_orders.get(item_id, [])),
            "sell_orders": len(self.sell_orders.get(item_id, [])),
        }

    def get_order_book_status(self, item_id: str) -> Dict[str, Any]:
        """주어진 아이템의 현재 호가창 상태를 반환합니다."""
        return {
            "buy_orders": [
                {"agent_id": o.agent_id, "quantity": o.quantity, "price": o.price}
                for o in self.buy_orders.get(item_id, [])
            ],
            "sell_orders": [
                {"agent_id": o.agent_id, "quantity": o.quantity, "price": o.price}
                for o in self.sell_orders.get(item_id, [])
            ],
        }

    def get_all_bids(self, item_id: str) -> List[Order]:
        """주어진 아이템의 모든 매수 주문을 반환합니다."""
        return self.buy_orders.get(item_id, [])

    def get_all_asks(self, item_id: str) -> List[Order]:
        """주어진 아이템의 모든 매도 주문을 반환합니다."""
        return self.sell_orders.get(item_id, [])

    def get_total_demand(self) -> float:
        """시장의 모든 매수 주문 총량을 반환합니다."""
        return sum(
            order.quantity for orders in self.buy_orders.values() for order in orders
        )

    def get_total_supply(self) -> float:
        """시장의 모든 매도 주문 총량을 반환합니다."""
        return sum(
            order.quantity for orders in self.sell_orders.values() for order in orders
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
