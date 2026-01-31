from typing import List, Any, Optional
import random
from simulation.models import StockOrder

class StockTrader:
    """
    Executes stock buy/sell logic.
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def _get_stock_price(self, market_snapshot: Any, firm_id: int) -> float:
        key = f"stock_{firm_id}"
        price = 0.0

        if not market_snapshot:
            return 0.0

        # Try market_signals first
        signals = getattr(market_snapshot, "market_signals", None)
        if isinstance(signals, dict):
             signal = signals.get(key)
             if signal:
                 price = getattr(signal, "last_traded_price", 0.0) or getattr(signal, "best_bid", 0.0) or 0.0

        # Fallback to market_data
        if price <= 0:
             m_data = getattr(market_snapshot, "market_data", None)
             if isinstance(m_data, dict):
                 stock_data = m_data.get("stock_market", {}).get(key, {})
                 price = stock_data.get("avg_price", 0.0)

        return price

    def place_buy_orders(self, household: Any, amount_to_invest: float, market_snapshot: Any, config: Any, logger: Optional[Any] = None) -> List[StockOrder]:
        orders = []

        if not market_snapshot:
            return orders

        # Identify available stocks
        available_stocks = []
        stock_keys = []
        
        m_data = getattr(market_snapshot, "market_data", None)
        if isinstance(m_data, dict) and "stock_market" in m_data:
             stock_keys.extend(m_data["stock_market"].keys())

        signals = getattr(market_snapshot, "market_signals", None)
        if isinstance(signals, dict):
             stock_keys.extend([k for k in signals.keys() if k.startswith("stock_")])

        stock_keys = list(set(stock_keys))

        for key in stock_keys:
            if key.startswith("stock_"):
                try:
                    fid = int(key.split("_")[1])
                    price = self._get_stock_price(market_snapshot, fid)
                    if price > 0:
                        available_stocks.append(fid)
                except Exception as e:
                    if logger:
                        logger.warning(f"STOCK_KEY_ERROR | Invalid stock key format '{key}': {e}")

        if not available_stocks:
            return orders

        diversification_count = config.stock_investment_diversification_count
        investment_per_stock = amount_to_invest / diversification_count
        for _ in range(diversification_count):
            firm_id = random.choice(available_stocks)
            price = self._get_stock_price(market_snapshot, firm_id)
            if price > 0:
                quantity = investment_per_stock / price
                if quantity >= 1.0:
                    order = StockOrder(household.id, order_type="BUY", firm_id=firm_id, quantity=quantity, price=price * 1.05)
                    orders.append(order)
        return orders

    def place_sell_orders(self, household: Any, amount_to_sell: float, market_snapshot: Any, config: Any, logger: Optional[Any] = None) -> List[StockOrder]:
        orders = []
        sorted_holdings = sorted(
            household.portfolio_holdings.items(),
            key=lambda item: item[1].quantity * self._get_stock_price(market_snapshot, item[0]), # Access .quantity
            reverse=True
        )

        for firm_id, share in sorted_holdings:
            quantity = share.quantity
            if amount_to_sell <= 0:
                break
            price = self._get_stock_price(market_snapshot, firm_id)
            if price > 0:
                value_of_holding = quantity * price
                sell_value = min(amount_to_sell, value_of_holding)
                sell_quantity = sell_value / price
                if sell_quantity >= 1.0:
                    order = StockOrder(household.id, order_type="SELL", firm_id=firm_id, quantity=sell_quantity, price=price * 0.95)
                    orders.append(order)
                    amount_to_sell -= sell_value
        return orders
