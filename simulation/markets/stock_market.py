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
from modules.market.api import OrderDTO
from modules.finance.api import IShareholderRegistry

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

@dataclass
class ManagedOrder:
    """A mutable wrapper for an immutable OrderDTO to manage its state within the order book."""
    order: OrderDTO
    remaining_quantity: float
    created_tick: int

class StockMarket(Market):
    """
    주식 시장 클래스.
    
    기업 주식의 매수/매도 주문을 관리하고, 거래를 매칭합니다.
    주가는 기업 순자산가치(Book Value) 기반으로 기준가를 설정하고,
    실제 거래는 호가 매칭으로 이루어집니다.
    """

    def __init__(
        self,
        config_module: Any,
        shareholder_registry: IShareholderRegistry,
        logger: Optional[logging.Logger] = None,
    ):
        self.id = "stock_market"
        self.config_module = config_module
        self.logger = logger or logging.getLogger(__name__)
        self.shareholder_registry = shareholder_registry
        
        # 기업별 주문서 (firm_id -> List[ManagedOrder])
        self.buy_orders: Dict[int, List[ManagedOrder]] = defaultdict(list)
        self.sell_orders: Dict[int, List[ManagedOrder]] = defaultdict(list)
        
        # 가격 및 거래량 추적
        self.last_prices: Dict[int, float] = {}      # 최근 거래가
        self.reference_prices: Dict[int, float] = {} # 기준가 (순자산가치 기반)
        self.daily_volumes: Dict[int, float] = {}    # 일일 거래량
        self.daily_high: Dict[int, float] = {}       # 일일 최고가
        self.daily_low: Dict[int, float] = {}        # 일일 최저가

    def update_shareholder(self, agent_id: int, firm_id: int, quantity: float) -> None:
        """
        주주 명부를 갱신합니다. (보유량 설정)
        Delegates to ShareholderRegistry (TD-275).
        """
        self.shareholder_registry.register_shares(firm_id, agent_id, quantity)

    def update_reference_prices(self, firms: Dict[int, "Firm"]) -> None:
        """
        기업들의 순자산가치를 기반으로 기준 주가를 업데이트합니다.
        
        Args:
            firms: 기업 ID -> Firm 객체 맵
        """
        multiplier = getattr(self.config_module, "STOCK_BOOK_VALUE_MULTIPLIER", 1.0)
        
        for firm_id, firm in firms.items():
            if not getattr(firm, "is_active", True):
                continue
                
            book_value = self._calculate_book_value_per_share(firm)
            self.reference_prices[firm_id] = max(0.01, book_value * multiplier)

    def _calculate_book_value_per_share(self, firm: "Firm") -> float:
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

    def get_daily_avg_price(self, firm_id: Optional[int] = None) -> float:
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
        return max(managed.order.price_limit for managed in orders)

    def get_best_ask(self, firm_id: int) -> Optional[float]:
        """특정 기업 주식의 최저 매도호가를 반환합니다."""
        orders = self.sell_orders.get(firm_id, [])
        if not orders:
            return None
        return min(managed.order.price_limit for managed in orders)

    def place_order(self, order: OrderDTO, tick: int) -> None:
        """
        주식 주문을 제출합니다.
        """
        if not isinstance(order, OrderDTO):
            self.logger.error(f"Invalid order type passed to StockMarket: {type(order)}. Expected OrderDTO.")
            return

        # item_id에서 firm_id 추출 ("stock_{firm_id}")
        try:
            firm_id = int(order.item_id.split("_")[1])
        except (ValueError, IndexError):
            self.logger.error(
                f"Invalid item_id format for stock order: {order.item_id}. Expected 'stock_<firm_id>'"
            )
            return

        # 가격 제한 확인 (상하한가)
        limit_rate = getattr(self.config_module, "STOCK_PRICE_LIMIT_RATE", 0.10)
        ref_price = self.reference_prices.get(firm_id, order.price_limit)
        
        min_price = ref_price * (1 - limit_rate)
        max_price = ref_price * (1 + limit_rate)
        
        final_order = order
        if order.price_limit < min_price or order.price_limit > max_price:
            self.logger.warning(
                f"Stock order price {order.price_limit:.2f} out of limit range "
                f"[{min_price:.2f}, {max_price:.2f}] for firm {firm_id}",
                extra={"tick": tick, "agent_id": order.agent_id, "firm_id": firm_id}
            )
            # 가격을 제한 범위 내로 조정하여 새로운 OrderDTO 생성
            clamped_price = max(min_price, min(max_price, order.price_limit))
            final_order = replace(order, price_limit=clamped_price)

        # 내부 래퍼 생성
        managed_order = ManagedOrder(
            order=final_order,
            remaining_quantity=final_order.quantity,
            created_tick=tick
        )
        
        # 주문 추가
        if final_order.side == "BUY":
            self.buy_orders[firm_id].append(managed_order)
            # 높은 가격 순으로 정렬
            self.buy_orders[firm_id].sort(key=lambda m: -m.order.price_limit)
        elif final_order.side == "SELL":
            self.sell_orders[firm_id].append(managed_order)
            # 낮은 가격 순으로 정렬
            self.sell_orders[firm_id].sort(key=lambda m: m.order.price_limit)
        else:
            self.logger.warning(
                f"Unknown stock order side: {final_order.side}",
                extra={"tick": tick, "agent_id": final_order.agent_id}
            )
            return
        
        self.logger.info(
            f"Stock {final_order.side} order placed: {final_order.quantity:.1f} shares "
            f"of firm {firm_id} at {final_order.price_limit:.2f}",
            extra={
                "tick": tick,
                "agent_id": final_order.agent_id,
                "firm_id": firm_id,
                "order_type": final_order.side,
                "quantity": final_order.quantity,
                "price": final_order.price_limit,
                "tags": ["stock", "order"]
            }
        )

    def match_orders(self, tick: int) -> List[Transaction]:
        """
        모든 기업의 주식 주문을 매칭하여 거래를 성사시킵니다.
        
        Args:
            tick: 현재 시뮬레이션 틱
            
        Returns:
            성사된 주식 거래 목록
        """
        all_transactions: List[Transaction] = []
        
        # 모든 기업에 대해 매칭 수행
        all_firm_ids = set(self.buy_orders.keys()) | set(self.sell_orders.keys())
        
        for firm_id in all_firm_ids:
            transactions = self._match_orders_for_firm(firm_id, tick)
            all_transactions.extend(transactions)
        
        return all_transactions

    def _match_orders_for_firm(self, firm_id: int, tick: int) -> List[Transaction]:
        """특정 기업의 주식 주문을 매칭합니다."""
        transactions: List[Transaction] = []
        
        buy_orders = self.buy_orders.get(firm_id, [])
        sell_orders = self.sell_orders.get(firm_id, [])
        
        while buy_orders and sell_orders:
            best_buy_managed = buy_orders[0]
            best_sell_managed = sell_orders[0]

            best_buy_dto = best_buy_managed.order
            best_sell_dto = best_sell_managed.order
            
            # 매수가 >= 매도가 이면 거래 성립
            if best_buy_dto.price_limit >= best_sell_dto.price_limit:
                # 거래 가격: 두 호가의 평균
                trade_price = (best_buy_dto.price_limit + best_sell_dto.price_limit) / 2
                trade_quantity = min(best_buy_managed.remaining_quantity, best_sell_managed.remaining_quantity)

                # Validation (Tech Debt Fix)
                if best_buy_dto.agent_id is None or best_sell_dto.agent_id is None:
                    self.logger.critical(
                        f"STOCK_MATCH_FATAL | NULL ID in matched order! "
                        f"BuyerID: {best_buy_dto.agent_id}, SellerID: {best_sell_dto.agent_id}. Skipping match.",
                        extra={"tick": tick, "firm_id": firm_id}
                    )
                    # Skip this match and possibly pop the problematic order?
                    # For safety, we just break or continue.
                    # If we don't pop, we infinite loop.
                    # We should pop the invalid one.
                    if best_buy_dto.agent_id is None:
                        buy_orders.pop(0)
                    if best_sell_dto.agent_id is None:
                        sell_orders.pop(0)
                    continue
                
                # 거래 생성
                transaction = Transaction(
                    buyer_id=best_buy_dto.agent_id,
                    seller_id=best_sell_dto.agent_id,
                    item_id=f"stock_{firm_id}",
                    quantity=trade_quantity,
                    price=trade_price,
                    market_id=self.id,
                    transaction_type="stock",
                    time=tick,
                )
                transactions.append(transaction)
                
                # 가격 및 거래량 업데이트
                self.last_prices[firm_id] = trade_price
                self.daily_volumes[firm_id] = self.daily_volumes.get(firm_id, 0) + trade_quantity
                
                # 일일 고저가 업데이트
                if firm_id not in self.daily_high or trade_price > self.daily_high[firm_id]:
                    self.daily_high[firm_id] = trade_price
                if firm_id not in self.daily_low or trade_price < self.daily_low[firm_id]:
                    self.daily_low[firm_id] = trade_price
                
                self.logger.info(
                    f"Stock trade: {trade_quantity:.1f} shares of firm {firm_id} "
                    f"at {trade_price:.2f} (buyer: {best_buy_dto.agent_id}, seller: {best_sell_dto.agent_id})",
                    extra={
                        "tick": tick,
                        "firm_id": firm_id,
                        "quantity": trade_quantity,
                        "price": trade_price,
                        "buyer_id": best_buy_dto.agent_id,
                        "seller_id": best_sell_dto.agent_id,
                        "tags": ["stock", "trade"]
                    }
                )
                
                # 주문 수량 조정 (ManagedOrder 내부 상태 변경)
                best_buy_managed.remaining_quantity -= trade_quantity
                best_sell_managed.remaining_quantity -= trade_quantity
                
                # 완료된 주문 제거
                if best_buy_managed.remaining_quantity <= 0:
                    buy_orders.pop(0)
                if best_sell_managed.remaining_quantity <= 0:
                    sell_orders.pop(0)
            else:
                # 더 이상 매칭 가능한 주문 없음
                break
        
        return transactions

    def clear_expired_orders(self, current_tick: int) -> int:
        """
        만료된 주문을 제거합니다.
        
        Args:
            current_tick: 현재 시뮬레이션 틱
            
        Returns:
            제거된 주문 수
        """
        expiry_ticks = getattr(self.config_module, "STOCK_ORDER_EXPIRY_TICKS", 5)
        removed_count = 0
        
        for firm_id in list(self.buy_orders.keys()):
            original_count = len(self.buy_orders[firm_id])
            self.buy_orders[firm_id] = [
                managed for managed in self.buy_orders[firm_id]
                if current_tick - managed.created_tick < expiry_ticks
            ]
            removed = original_count - len(self.buy_orders[firm_id])
            removed_count += removed
        
        for firm_id in list(self.sell_orders.keys()):
            original_count = len(self.sell_orders[firm_id])
            self.sell_orders[firm_id] = [
                managed for managed in self.sell_orders[firm_id]
                if current_tick - managed.created_tick < expiry_ticks
            ]
            removed = original_count - len(self.sell_orders[firm_id])
            removed_count += removed
        
        if removed_count > 0:
            self.logger.debug(
                f"Cleared {removed_count} expired stock orders",
                extra={"tick": current_tick, "tags": ["stock", "cleanup"]}
            )
        
        return removed_count

    def reset_daily_stats(self) -> None:
        """일일 통계를 초기화합니다."""
        self.daily_volumes.clear()
        self.daily_high.clear()
        self.daily_low.clear()

    def get_market_summary(self, firm_id: int) -> Dict[str, Any]:
        """특정 기업의 주식 시장 요약 정보를 반환합니다."""
        return {
            "firm_id": firm_id,
            "last_price": self.last_prices.get(firm_id),
            "reference_price": self.reference_prices.get(firm_id),
            "best_bid": self.get_best_bid(firm_id),
            "best_ask": self.get_best_ask(firm_id),
            "daily_volume": self.daily_volumes.get(firm_id, 0),
            "daily_high": self.daily_high.get(firm_id),
            "daily_low": self.daily_low.get(firm_id),
            "buy_order_count": len(self.buy_orders.get(firm_id, [])),
            "sell_order_count": len(self.sell_orders.get(firm_id, [])),
        }

    def clear_orders(self) -> None:
        """
        모든 주문을 초기화합니다.
        다른 시장과의 인터페이스 호환성을 위한 메서드입니다.
        """
        self.buy_orders.clear()
        self.sell_orders.clear()
        self.reset_daily_stats()
