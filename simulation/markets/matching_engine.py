from typing import List, Dict, Any, Optional, Tuple, Protocol
from dataclasses import replace
import logging
from modules.market.api import IMatchingEngine, OrderBookStateDTO, StockMarketStateDTO, MatchingResultDTO, CanonicalOrderDTO
from simulation.models import Transaction
logger = logging.getLogger(__name__)

class OrderBookMatchingEngine(IMatchingEngine):
    """
    Stateless matching engine for Goods and Labor markets.
    Implements price-time priority and targeted (brand loyalty) matching.
    Uses Integer Math (Pennies) for Zero-Sum Integrity.
    """

    def match(self, state: OrderBookStateDTO, current_tick: int) -> MatchingResultDTO:
        all_transactions: List[Transaction] = []
        unfilled_buy_orders: Dict[str, List[CanonicalOrderDTO]] = {}
        unfilled_sell_orders: Dict[str, List[CanonicalOrderDTO]] = {}
        market_stats: Dict[str, Any] = {'last_traded_prices': {}, 'last_trade_ticks': {}, 'daily_total_volume': {}}
        all_item_ids = set(state.buy_orders.keys()) | set(state.sell_orders.keys())
        for item_id in all_item_ids:
            buy_orders = state.buy_orders.get(item_id, [])
            sell_orders = state.sell_orders.get(item_id, [])
            if not buy_orders or not sell_orders:
                unfilled_buy_orders[item_id] = buy_orders
                unfilled_sell_orders[item_id] = sell_orders
                continue
            transactions, remaining_buys, remaining_sells, stats = self._match_item(item_id, buy_orders, sell_orders, state.market_id, current_tick)
            all_transactions.extend(transactions)
            unfilled_buy_orders[item_id] = remaining_buys
            unfilled_sell_orders[item_id] = remaining_sells
            for k, v in stats.items():
                if k == 'volume':
                    if item_id not in market_stats['daily_total_volume']:
                        market_stats['daily_total_volume'][item_id] = 0.0
                    market_stats['daily_total_volume'][item_id] += v
                elif k == 'last_price':
                    market_stats['last_traded_prices'][item_id] = v
                    market_stats['last_trade_ticks'][item_id] = current_tick
        return MatchingResultDTO(transactions=all_transactions, unfilled_buy_orders=unfilled_buy_orders, unfilled_sell_orders=unfilled_sell_orders, market_stats=market_stats)

    def _match_item(self, item_id: str, buy_orders: List[CanonicalOrderDTO], sell_orders: List[CanonicalOrderDTO], market_id: str, current_tick: int) -> Tuple[List[Transaction], List[CanonicalOrderDTO], List[CanonicalOrderDTO], Dict[str, Any]]:
        transactions: List[Transaction] = []
        stats: Dict[str, Any] = {'volume': 0.0}
        targeted_buys = [o for o in buy_orders if o.target_agent_id is not None]
        general_buys = [o for o in buy_orders if o.target_agent_id is None]
        general_buys.sort(key=lambda o: o.price_pennies, reverse=True)
        sell_map: Dict[int, List[CanonicalOrderDTO]] = {}
        for s_order in sell_orders:
            agent_id = int(s_order.agent_id) if isinstance(s_order.agent_id, (int, float)) else s_order.agent_id
            if agent_id not in sell_map:
                sell_map[agent_id] = []
            sell_map[agent_id].append(s_order)

        class MutableOrder:

            def __init__(self, dto: CanonicalOrderDTO):
                self.dto = dto
                self.remaining_qty = dto.quantity

            def to_dto(self) -> CanonicalOrderDTO:
                return replace(self.dto, quantity=self.remaining_qty)
        mutable_targeted_buys = [MutableOrder(o) for o in targeted_buys]
        mutable_general_buys = [MutableOrder(o) for o in general_buys]
        mutable_sell_map: Dict[Any, List[MutableOrder]] = {}
        all_mutable_sells: List[MutableOrder] = []
        for s_list in sell_map.values():
            s_list.sort(key=lambda o: o.price_pennies)
            m_list = [MutableOrder(o) for o in s_list]
            mutable_sell_map[s_list[0].agent_id] = m_list
            all_mutable_sells.extend(m_list)
        remaining_targeted_buys: List[MutableOrder] = []
        for b_wrapper in mutable_targeted_buys:
            target_id = b_wrapper.dto.target_agent_id
            target_asks = mutable_sell_map.get(target_id)
            if target_asks:
                for s_wrapper in target_asks:
                    if b_wrapper.remaining_qty <= 1e-09:
                        break
                    if s_wrapper.remaining_qty <= 1e-09:
                        continue
                    if b_wrapper.dto.price_pennies >= s_wrapper.dto.price_pennies:
                        trade_price_pennies = s_wrapper.dto.price_pennies
                        trade_qty = min(b_wrapper.remaining_qty, s_wrapper.remaining_qty)
                        trade_total_pennies = int(trade_price_pennies * trade_qty)
                        effective_price_dollars = trade_total_pennies / trade_qty / 100.0 if trade_qty > 0 else 0.0
                        tx = Transaction(item_id=item_id, quantity=trade_qty, price=effective_price_dollars, total_pennies=trade_total_pennies, buyer_id=b_wrapper.dto.agent_id, seller_id=s_wrapper.dto.agent_id, market_id=market_id, transaction_type='labor' if 'labor' in market_id else 'housing' if 'housing' in market_id else 'goods', time=current_tick, quality=s_wrapper.dto.brand_info.get('quality', 1.0) if s_wrapper.dto.brand_info else 1.0)
                        transactions.append(tx)
                        stats['last_price'] = effective_price_dollars
                        stats['volume'] += trade_qty
                        b_wrapper.remaining_qty -= trade_qty
                        s_wrapper.remaining_qty -= trade_qty
            if b_wrapper.remaining_qty > 1e-09:
                remaining_targeted_buys.append(b_wrapper)
        if remaining_targeted_buys:
            mutable_general_buys.extend(remaining_targeted_buys)
            mutable_general_buys.sort(key=lambda o: o.dto.price_pennies, reverse=True)
        active_sells = [s for s in all_mutable_sells if s.remaining_qty > 1e-09]
        active_sells.sort(key=lambda o: o.dto.price_pennies)
        idx_b = 0
        idx_s = 0
        while idx_b < len(mutable_general_buys) and idx_s < len(active_sells):
            b_wrapper = mutable_general_buys[idx_b]
            s_wrapper = active_sells[idx_s]
            if b_wrapper.remaining_qty <= 1e-09:
                idx_b += 1
                continue
            if s_wrapper.remaining_qty <= 1e-09:
                idx_s += 1
                continue
            if b_wrapper.dto.price_pennies >= s_wrapper.dto.price_pennies:
                if market_id == 'labor' or market_id == 'research_labor':
                    trade_price_pennies = b_wrapper.dto.price_pennies
                else:
                    trade_price_pennies = (b_wrapper.dto.price_pennies + s_wrapper.dto.price_pennies) // 2
                trade_qty = min(b_wrapper.remaining_qty, s_wrapper.remaining_qty)
                trade_total_pennies = int(trade_price_pennies * trade_qty)
                effective_price_dollars = trade_total_pennies / trade_qty / 100.0 if trade_qty > 0 else 0.0
                tx = Transaction(item_id=item_id, quantity=trade_qty, price=effective_price_dollars, total_pennies=trade_total_pennies, buyer_id=b_wrapper.dto.agent_id, seller_id=s_wrapper.dto.agent_id, market_id=market_id, transaction_type='labor' if 'labor' in market_id else 'housing' if 'housing' in market_id else 'goods', time=current_tick, quality=s_wrapper.dto.brand_info.get('quality', 1.0) if s_wrapper.dto.brand_info else 1.0)
                transactions.append(tx)
                stats['last_price'] = effective_price_dollars
                stats['volume'] += trade_qty
                b_wrapper.remaining_qty -= trade_qty
                s_wrapper.remaining_qty -= trade_qty
            else:
                break
        final_buys = [b.to_dto() for b in mutable_general_buys if b.remaining_qty > 1e-09]
        final_buys.sort(key=lambda o: o.price_pennies, reverse=True)
        final_sells = [s.to_dto() for s in active_sells if s.remaining_qty > 1e-09]
        final_sells.sort(key=lambda o: o.price_pennies)
        return (transactions, final_buys, final_sells, stats)

class StockMatchingEngine(IMatchingEngine):
    """
    Stateless matching engine for Stock Market.
    Matches Buy and Sell orders for each firm.
    Uses Integer Math (Pennies).
    """

    def match(self, state: StockMarketStateDTO, current_tick: int) -> MatchingResultDTO:
        all_transactions: List[Transaction] = []
        unfilled_buy_orders: Dict[str, List[CanonicalOrderDTO]] = {}
        unfilled_sell_orders: Dict[str, List[CanonicalOrderDTO]] = {}
        market_stats: Dict[str, Any] = {'last_prices': {}, 'daily_volumes': {}, 'daily_high': {}, 'daily_low': {}}
        all_firm_ids = set(state.buy_orders.keys()) | set(state.sell_orders.keys())
        for firm_id in all_firm_ids:
            buy_orders = state.buy_orders.get(firm_id, [])
            sell_orders = state.sell_orders.get(firm_id, [])
            if not buy_orders or not sell_orders:
                unfilled_buy_orders[str(firm_id)] = buy_orders
                unfilled_sell_orders[str(firm_id)] = sell_orders
                continue
            transactions, remaining_buys, remaining_sells, stats = self._match_firm_stock(firm_id, buy_orders, sell_orders, state.market_id, current_tick)
            all_transactions.extend(transactions)
            unfilled_buy_orders[str(firm_id)] = remaining_buys
            unfilled_sell_orders[str(firm_id)] = remaining_sells
            if 'last_price' in stats:
                market_stats['last_prices'][firm_id] = stats['last_price']
                market_stats['daily_volumes'][firm_id] = stats['volume']
                market_stats['daily_high'][firm_id] = stats['high']
                market_stats['daily_low'][firm_id] = stats['low']
        return MatchingResultDTO(transactions=all_transactions, unfilled_buy_orders=unfilled_buy_orders, unfilled_sell_orders=unfilled_sell_orders, market_stats=market_stats)

    def _match_firm_stock(self, firm_id: int, buy_orders: List[CanonicalOrderDTO], sell_orders: List[CanonicalOrderDTO], market_id: str, current_tick: int) -> Tuple[List[Transaction], List[CanonicalOrderDTO], List[CanonicalOrderDTO], Dict[str, Any]]:
        transactions: List[Transaction] = []
        stats: Dict[str, Any] = {'volume': 0.0}
        buy_orders.sort(key=lambda o: o.price_pennies, reverse=True)
        sell_orders.sort(key=lambda o: o.price_pennies)

        class MutableOrder:

            def __init__(self, dto: CanonicalOrderDTO):
                self.dto = dto
                self.remaining_qty = dto.quantity

            def to_dto(self) -> CanonicalOrderDTO:
                return replace(self.dto, quantity=self.remaining_qty)
        m_buys = [MutableOrder(o) for o in buy_orders]
        m_sells = [MutableOrder(o) for o in sell_orders]
        idx_b = 0
        idx_s = 0
        last_price = None
        high = -float('inf')
        low = float('inf')
        while idx_b < len(m_buys) and idx_s < len(m_sells):
            b_order = m_buys[idx_b]
            s_order = m_sells[idx_s]
            if b_order.remaining_qty <= 1e-09:
                idx_b += 1
                continue
            if s_order.remaining_qty <= 1e-09:
                idx_s += 1
                continue
            if b_order.dto.price_pennies >= s_order.dto.price_pennies:
                trade_price_pennies = (b_order.dto.price_pennies + s_order.dto.price_pennies) // 2
                trade_qty = min(b_order.remaining_qty, s_order.remaining_qty)
                trade_total_pennies = int(trade_price_pennies * trade_qty)
                effective_price_dollars = trade_total_pennies / trade_qty / 100.0 if trade_qty > 0 else 0.0
                if b_order.dto.agent_id is None or s_order.dto.agent_id is None:
                    if b_order.dto.agent_id is None:
                        idx_b += 1
                    if s_order.dto.agent_id is None:
                        idx_s += 1
                    continue
                tx = Transaction(buyer_id=b_order.dto.agent_id, seller_id=s_order.dto.agent_id, item_id=f'stock_{firm_id}', quantity=trade_qty, price=effective_price_dollars, total_pennies=trade_total_pennies, market_id=market_id, transaction_type='stock', time=current_tick)
                transactions.append(tx)
                stats['volume'] += trade_qty
                last_price = effective_price_dollars
                high = max(high, effective_price_dollars)
                low = min(low, effective_price_dollars)
                b_order.remaining_qty -= trade_qty
                s_order.remaining_qty -= trade_qty
            else:
                break
        final_buys = [o.to_dto() for o in m_buys if o.remaining_qty > 1e-09]
        final_sells = [o.to_dto() for o in m_sells if o.remaining_qty > 1e-09]
        if last_price is not None:
            stats['last_price'] = last_price
            stats['high'] = high
            stats['low'] = low
        return (transactions, final_buys, final_sells, stats)