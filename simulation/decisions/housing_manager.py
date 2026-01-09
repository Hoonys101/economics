from typing import TYPE_CHECKING, Dict, Any
import math

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.markets.order_book_market import OrderBookMarket

class HousingManager:
    """
    Manages the logic for Rent vs Buy decisions for Households.
    Implements NPV-based decision making.
    """

    @staticmethod
    def should_buy(
        household: "Household",
        unit_price: float,
        rent_price: float,
        interest_rate: float = 0.05,
        horizon: int = 120,
        discount_rate: float = 0.0005, # 0.05% per tick ~ 5% per year (100 ticks)
        maintenance_rate: float = 0.001,
        appreciation_rate: float = 0.002
    ) -> bool:
        """
        Determines if buying is financially superior to renting based on NPV.

        Args:
            household: The household agent.
            unit_price: The asking price of the property.
            rent_price: The monthly (tickly) rent price for a comparable unit.
            interest_rate: Annual interest rate (0.05 = 5%).
            horizon: Investment horizon in ticks (e.g., 120 ticks).
            discount_rate: Per-tick discount rate.
            maintenance_rate: Per-tick maintenance cost as ratio of value.
            appreciation_rate: Per-tick property appreciation rate.

        Returns:
            True if Buy NPV > Rent NPV.
        """
        # Convert Annual Rate to Tick Rate
        # Assuming TICKS_PER_YEAR is roughly 100
        tick_interest_rate = interest_rate / 100.0

        # Rent NPV (Cost of Renting)
        # Sum of discounted rent payments
        # Formula: Rent * (1 - (1+r)^-n) / r
        # Approximation for loop:
        rent_npv = 0.0
        for t in range(1, horizon + 1):
            rent_npv += rent_price / ((1 + discount_rate) ** t)

        # Buy NPV
        # Costs: Down Payment + Mortgage Payments + Maintenance
        # Gains: Asset Value at Horizon (Appreciated) - Remaining Principal

        ltv = 0.8
        down_payment = unit_price * (1 - ltv)
        loan_amount = unit_price * ltv

        # Mortgage Payment (Interest Only for simplicity or Amortized)
        # Spec implies Amortization logic in Bank, but for decision making we can approximate.
        # Let's use simple interest + principal/horizon approximation or standard PMT formula.
        # PMT = P * r * (1+r)^n / ((1+r)^n - 1)
        # Where r = tick_interest_rate, n = 360 (Mortgage Term)
        # Even if horizon is 120, mortgage term is usually longer (30 years = 3000 ticks? Spec says 360 ticks).
        mortgage_term = 360

        if tick_interest_rate > 0:
            factor = (1 + tick_interest_rate) ** mortgage_term
            monthly_payment = loan_amount * tick_interest_rate * factor / (factor - 1)
        else:
            monthly_payment = loan_amount / mortgage_term

        buy_cost_npv = down_payment
        for t in range(1, horizon + 1):
            maintenance_cost = unit_price * maintenance_rate
            cost = monthly_payment + maintenance_cost
            buy_cost_npv += cost / ((1 + discount_rate) ** t)

        # Terminal Value
        future_value = unit_price * ((1 + appreciation_rate) ** horizon)

        # Remaining Principal at Horizon
        # Needed to pay off loan if sold at horizon
        # Approximation: if term > horizon, we owe money.
        # Exact calculation requires amortization schedule.
        # Let's approximate remaining principal roughly linearly for decision speed
        paid_principal_ratio = min(1.0, horizon / mortgage_term)
        remaining_principal = loan_amount * (1 - paid_principal_ratio)

        net_terminal_value = future_value - remaining_principal
        discounted_terminal_value = net_terminal_value / ((1 + discount_rate) ** horizon)

        total_buy_cost_net = buy_cost_npv - discounted_terminal_value

        # If Total Net Cost of Buying < Cost of Renting, then BUY.
        return total_buy_cost_net < rent_npv

    @staticmethod
    def find_best_property(market: "OrderBookMarket", budget: float) -> str | None:
        """
        Scans the 'real_estate' market order book for the best property ID.
        For V1, simply returns the cheapest unit that fits the budget (20% down payment).

        Args:
            market: The real_estate market instance.
            budget: The household's current liquid assets.

        Returns:
            item_id string (e.g. "unit_5") or None.
        """
        # Iterate over all sell orders
        # market.sell_orders is Dict[item_id, List[Order]]
        best_item_id = None
        best_price = float('inf')

        for item_id, orders in market.sell_orders.items():
            if not orders:
                continue

            # Cheapest ask for this unit
            # Assumes orders are sorted by price ascending
            ask_price = orders[0].price

            # Check affordability (20% down payment)
            required_down = ask_price * 0.2
            if budget >= required_down:
                if ask_price < best_price:
                    best_price = ask_price
                    best_item_id = item_id

        return best_item_id
