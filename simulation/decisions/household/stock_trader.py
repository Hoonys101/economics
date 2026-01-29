from typing import List, Any, Optional
import random
from simulation.models import StockOrder

class StockTrader:
    """
    Executes stock buy/sell logic.
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def place_buy_orders(self, household: Any, amount_to_invest: float, market_snapshot: Any, config: Any, logger: Optional[Any] = None) -> List[StockOrder]:
        orders = []
        # Filter stock prices from snapshot
        available_stocks = []
        for key, price in market_snapshot.prices.items():
            if key.startswith("stock_") and price > 0:
                try:
                    fid = int(key.split("_")[1])
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
            price = market_snapshot.prices.get(f"stock_{firm_id}", 0.0)
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
            key=lambda item: item[1].quantity * market_snapshot.prices.get(f"stock_{item[0]}", 0.0), # Access .quantity
            reverse=True
        )

        for firm_id, share in sorted_holdings:
            quantity = share.quantity
            if amount_to_sell <= 0:
                break
            price = market_snapshot.prices.get(f"stock_{firm_id}", 0.0)
            if price > 0:
                value_of_holding = quantity * price
                sell_value = min(amount_to_sell, value_of_holding)
                sell_quantity = sell_value / price
                if sell_quantity >= 1.0:
                    order = StockOrder(household.id, order_type="SELL", firm_id=firm_id, quantity=sell_quantity, price=price * 0.95)
                    orders.append(order)
                    amount_to_sell -= sell_value
        return orders
