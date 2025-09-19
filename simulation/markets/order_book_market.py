from typing import List, Dict, Any
import logging

from simulation.models import Order, Transaction
from simulation.core_markets import Market

logger = logging.getLogger(__name__)

class OrderBookMarket(Market):
    """호가창(Order Book) 기반의 시장을 시뮬레이션하는 클래스.

    매수/매도 주문을 접수하고, 가격 우선 및 시간 우선 원칙에 따라 주문을 매칭하여 거래를 체결합니다.
    """
    def __init__(self, market_id: str, logger: logging.Logger = None):
        """OrderBookMarket을 초기화합니다.

        Args:
            market_id (str): 시장의 고유 ID (예: 'goods_market', 'labor_market').
            logger (logging.Logger, optional): 로깅을 위한 Logger 인스턴스. 기본값은 None.
        """
        self.market_id = market_id
        self.logger = logger if logger else logging.getLogger(__name__)
        self.buy_orders: Dict[str, List[Order]] = {}
        self.sell_orders: Dict[str, List[Order]] = {}
        self.logger.info(f"OrderBookMarket {self.market_id} initialized.", extra={'tick': 0, 'market_id': self.market_id, 'tags': ['init', 'market']})

    def clear_market_for_next_tick(self):
        """다음 틱을 위해 호가창을 초기화합니다."""
        self.buy_orders = {}
        self.sell_orders = {}
        self.logger.debug(f"Market {self.market_id} cleared for next tick.", extra={'market_id': self.market_id, 'tags': ['market_clear']})

    def place_order(self, order: Order):
        """시장에 주문을 제출합니다. 매칭은 별도의 메서드로 처리됩니다.

        Args:
            order (Order): 제출할 주문 객체.
        """
        log_extra = {'market_id': self.market_id, 'agent_id': order.agent_id, 'item_id': order.item_id, 'order_type': order.order_type, 'price': order.price, 'quantity': order.quantity}
        self.logger.debug(f"Placing order: {order.order_type} {order.quantity} of {order.item_id} at {order.price} by {order.agent_id}", extra=log_extra)
        self._add_order(order)

    def match_and_execute_orders(self, current_tick: int) -> List[Transaction]:
        """해당 틱에 제출된 모든 주문을 매칭하고 거래를 체결합니다.

        Returns:
            List[Transaction]: 발생한 모든 거래의 리스트.
        """
        transactions = []
        all_item_ids = set(self.buy_orders.keys()) | set(self.sell_orders.keys())
        for item_id in all_item_ids:
            transactions.extend(self._match_orders_for_item(item_id, current_tick))
        return transactions

    def _add_order(self, order: Order):
        # Determine which order book to use based on order type
        if order.order_type == 'BUY':
            target_order_book = self.buy_orders
        elif order.order_type == 'SELL':
            target_order_book = self.sell_orders
        else:
            self.logger.warning(f"Unknown order type for _add_order: {order.order_type}", extra={'order_type': order.order_type})
            return

        if order.item_id not in target_order_book:
            target_order_book[order.item_id] = []
        target_order_book[order.item_id].append(order)
        # Sort orders: BUY by price (desc), SELL by price (asc)
        if order.order_type == 'BUY':
            target_order_book[order.item_id].sort(key=lambda o: o.price, reverse=True)
        else:
            target_order_book[order.item_id].sort(key=lambda o: o.price)

    def _match_orders_for_item(self, item_id: str, current_tick: int) -> List[Transaction]:
        """주어진 아이템에 대해 매수/매도 주문을 매칭하고 거래를 체결합니다.

        Args:
            item_id (str): 매칭을 시도할 아이템의 ID.
            current_tick (int): 현재 시뮬레이션 틱.
        Returns:
            List[Transaction]: 해당 아이템에 대해 발생한 거래 리스트.
        """
        transactions = []
        buy_orders = self.buy_orders.get(item_id, [])
        sell_orders = self.sell_orders.get(item_id, [])

        log_extra = {'tick': current_tick, 'market_id': self.market_id, 'item_id': item_id}

        # --- GEMINI_DEBUG_START ---
        if item_id == 'labor': # Only log for labor market
            self.logger.info(f"MATCHING_DEBUG | Item: {item_id}, #Buy: {len(buy_orders)}, #Sell: {len(sell_orders)}", extra=log_extra)
            if buy_orders and sell_orders:
                self.logger.info(f"MATCHING_DEBUG | Best Bid: {buy_orders[0].price:.2f}, Best Ask: {sell_orders[0].price:.2f}", extra=log_extra)
            else:
                self.logger.info(f"MATCHING_DEBUG | Item: {item_id}, No matching orders (Buy: {len(buy_orders)}, Sell: {len(sell_orders)})", extra=log_extra)
        # --- GEMINI_DEBUG_END ---

        while buy_orders and sell_orders and buy_orders[0].price >= sell_orders[0].price:
            buy_order = buy_orders[0]
            sell_order = sell_orders[0]

            trade_price = (buy_order.price + sell_order.price) / 2 # Mid-price
            trade_quantity = min(buy_order.quantity, sell_order.quantity)

            transaction = Transaction(
                item_id=item_id,
                quantity=trade_quantity,
                price=trade_price,
                buyer_id=buy_order.agent_id,
                seller_id=sell_order.agent_id,
                market_id=self.market_id,
                transaction_type='goods' if self.market_id == 'goods_market' else 'labor',
                time=current_tick
            )
            transactions.append(transaction)

            self.logger.info(f"Matched {trade_quantity:.2f} of {item_id} at {trade_price:.2f}. Buyer: {buy_order.agent_id}, Seller: {sell_order.agent_id}", extra={
                **log_extra, 
                'buyer_id': buy_order.agent_id, 
                'seller_id': sell_order.agent_id, 
                'quantity': trade_quantity, 
                'price': trade_price, 
                'tags': ['match']
            })

            buy_order.quantity -= trade_quantity
            sell_order.quantity -= trade_quantity

            if buy_order.quantity <= 0:
                buy_orders.pop(0)
            if sell_order.quantity <= 0:
                sell_orders.pop(0)
        
        return transactions

    def get_best_ask(self, item_id: str) -> float | None:
        """주어진 아이템의 최저 판매 가격(best ask)을 반환합니다."""
        if item_id in self.sell_orders and self.sell_orders[item_id]:
            return self.sell_orders[item_id][0].price
        return None

    def get_best_bid(self, item_id: str) -> float | None:
        """주어진 아이템의 최고 구매 가격(best bid)을 반환합니다."""
        if item_id in self.buy_orders and self.buy_orders[item_id]:
            return self.buy_orders[item_id][0].price
        return None

    def get_order_book_status(self, item_id: str) -> Dict[str, Any]:
        """주어진 아이템의 현재 호가창 상태를 반환합니다."""
        return {
            "buy_orders": [{'agent_id': o.agent_id, 'quantity': o.quantity, 'price': o.price} for o in self.buy_orders.get(item_id, [])],
            "sell_orders": [{'agent_id': o.agent_id, 'quantity': o.quantity, 'price': o.price} for o in self.sell_orders.get(item_id, [])]
        }