from typing import List, Dict, Any, Optional
import math
from simulation.db.repository import SimulationRepository
from simulation.core_markets import Market
from simulation.markets.order_book_market import OrderBookMarket
import logging


class EconomicIndicatorsViewModel:
    """
    ViewModel for providing economic indicator data to the Web UI.
    Retrives data via SimulationRepository and processes it into the required format.
    """

    def __init__(self, repository: SimulationRepository):
        self.repository = repository

    def get_economic_indicators(
        self, start_tick: Optional[int] = None, end_tick: Optional[int] = None, run_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves and returns economic indicator data.
        """
        indicators = self.repository.analytics.get_economic_indicators(start_tick, end_tick, run_id=run_id)
        return indicators

    def get_wealth_distribution(self, households: List[Any], firms: List[Any]) -> Dict[str, Any]:
        """
        Calculates the wealth distribution (histogram buckets).
        """
        all_assets = [h._econ_state.assets for h in households] + [f.assets for f in firms]
        if not all_assets:
            return {"labels": [], "data": []}

        min_asset = min(all_assets)
        max_asset = max(all_assets)

        # Determine appropriate bucket size
        num_buckets = 10
        if max_asset == min_asset:
             return {"labels": [f"{min_asset:.0f}"], "data": [len(all_assets)]}

        bucket_size = (max_asset - min_asset) / num_buckets

        buckets = [0] * num_buckets
        labels = []

        for i in range(num_buckets):
            lower = min_asset + i * bucket_size
            upper = min_asset + (i + 1) * bucket_size
            labels.append(f"{lower:.0f}-{upper:.0f}")

        for asset in all_assets:
            index = int((asset - min_asset) / bucket_size)
            if index >= num_buckets:
                index = num_buckets - 1
            buckets[index] += 1

        return {
            "labels": labels,
            "data": buckets
        }

    def get_needs_distribution(self, households: List[Any], firms: List[Any]) -> Dict[str, Any]:
        """
        Calculates average needs for households and firms.
        """
        household_needs = {}
        household_count = len(households)
        if household_count > 0:
            # Initialize with keys from first household
            first_h = households[0]
            for key in first_h.needs.keys():
                household_needs[key] = 0.0

            for h in households:
                for key, value in h._bio_state.needs.items():
                    household_needs[key] += value

            for key in household_needs:
                household_needs[key] /= household_count

        firm_needs = {}
        # Firms typically don't have 'needs' dict in the same way, but let's check.
        # Firm class has 'liquidity_need' and maybe others depending on implementation.
        # Based on config, firms have liquidity need.
        firm_count = len(firms)
        if firm_count > 0:
            # Firm needs are stored in 'needs' dict just like households in BaseAgent
            total_liquidity_need = sum(f.needs.get('liquidity_need', 0) for f in firms)
            firm_needs['liquidity_need'] = total_liquidity_need / firm_count

        return {
            "household": household_needs,
            "firm": firm_needs
        }

    def get_sales_by_good(self, transactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Aggregates sales volume by good type from a list of transactions (dicts).
        """
        sales: Dict[str, float] = {}
        for tx in transactions:
            item = tx.get('item_id', 'unknown')
            qty = tx.get('quantity', 0)
            sales[item] = sales.get(item, 0) + qty
        return sales

    def get_market_order_book(self, markets: Dict[str, Market]) -> List[Dict[str, Any]]:
        """
        Extracts open orders from markets.
        """
        order_book = []
        for market_id, market in markets.items():
            if isinstance(market, OrderBookMarket):
                # We can access buy_orders and sell_orders directly if they are public
                # OrderBookMarket has .buy_orders: Dict[str, List[Order]]

                # Bids
                for item_id, orders in market.buy_orders.items():
                    for order in orders:
                        order_book.append({
                            "type": "BID",
                            "market_id": market_id,
                            "item_id": item_id,
                            "agent_id": order.agent_id,
                            "price": order.price,
                            "quantity": order.quantity
                        })

                # Asks
                for item_id, orders in market.sell_orders.items():
                    for order in orders:
                        order_book.append({
                            "type": "ASK",
                            "market_id": market_id,
                            "item_id": item_id,
                            "agent_id": order.agent_id,
                            "price": order.price,
                            "quantity": order.quantity
                        })

        # Sort by price descending for display? Or just return list.
        # Let's return list, frontend can sort.
        return order_book

    def get_unemployment_rate_data(
        self, start_tick: Optional[int] = None, end_tick: Optional[int] = None
    ) -> Dict[str, List[Any]]:
        """
        Unemployment rate data for Chart.js
        """
        indicators = self.get_economic_indicators(start_tick, end_tick)
        times = [ind["time"] for ind in indicators]
        unemployment_rates = [ind["unemployment_rate"] for ind in indicators]

        return {
            "labels": times,
            "datasets": [
                {
                    "label": "Unemployment Rate",
                    "data": unemployment_rates,
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1,
                }
            ],
        }
