from typing import Any, Dict, Optional, NamedTuple, Tuple
from enum import Enum
import math
import logging
from collections import deque

logger = logging.getLogger(__name__)

class MarketTrend(Enum):
    RISING = "RISING"
    FLAT = "FLAT"
    FALLING = "FALLING"

class HousingDecisionInputs(NamedTuple):
    current_wealth: float
    annual_income: float
    market_rent_monthly: float
    market_price: float
    risk_free_rate: float
    price_growth_expectation: float

class HouseholdSystem2Planner:
    """
    Household System 2 Planner (Specialized for Housing).
    Implements WO-046 Adaptive Housing Brain.
    """

    def __init__(self, agent: Any, config_module: Any):
        self.agent = agent
        self.config = config_module

    def calculate_housing_npv(self, inputs: HousingDecisionInputs) -> Dict[str, float]:
        """
        Calculates NPV for Buying vs Renting based on WO-046 formulas.

        Formulas:
        NPV_Buy = Sum( (U_shelter - Cost_own) / (1+r)^t ) + P_future / (1+r)^T - P_initial
        NPV_Rent = Sum( (Income_invest - Cost_rent) / (1+r)^t ) + Principal / (1+r)^T
        """

        # Parameters
        T_years = 10
        T_months = T_years * 12

        # Monthly Discount Rate
        # r = (interest_rate + 0.02) / 12
        r_monthly = (inputs.risk_free_rate + 0.02) / 12.0

        # Buying Components
        P_initial = inputs.market_price
        U_shelter = inputs.market_rent_monthly
        Cost_own = (P_initial * 0.01) / 12.0 # 1% annual maintenance

        # Price Growth Expectation (Capped at 5%)
        g_annual = min(inputs.price_growth_expectation, getattr(self.config, "HOUSING_EXPECTATION_CAP", 0.05))
        P_future = P_initial * ((1.0 + g_annual) ** T_years)

        # Renting Components
        # Principal = Down Payment (Assumed 20% of market_price)
        Principal = P_initial * 0.2
        # Income_invest = Principal * (interest_rate / 12)
        Income_invest = Principal * (inputs.risk_free_rate / 12.0)
        Cost_rent = inputs.market_rent_monthly

        # Calculate NPVs
        npv_buy_flow = 0.0
        npv_rent_flow = 0.0

        for t in range(1, T_months + 1):
            discount_factor = (1.0 + r_monthly) ** t

            # Buy Flow
            flow_buy = U_shelter - Cost_own
            npv_buy_flow += flow_buy / discount_factor

            # Rent Flow
            flow_rent = Income_invest - Cost_rent
            npv_rent_flow += flow_rent / discount_factor

        # Terminal Value Discounted
        terminal_discount = (1.0 + r_monthly) ** T_months

        term_val_buy = P_future / terminal_discount
        npv_buy = npv_buy_flow + term_val_buy - P_initial

        term_val_rent = Principal / terminal_discount
        npv_rent = npv_rent_flow + term_val_rent
        # Note: Rent NPV usually accounts for the Principal being preserved/invested.
        # The formula: Sum(Income - Rent) + Principal_Future.
        # Here Principal is simply returned?
        # Spec: "Principal / (1+r)^T".
        # This implies the principal grows at 0%? Or is Income_invest paying out the interest?
        # Yes, Income_invest is the monthly payout. The Principal remains intact.

        return {
            "npv_buy": npv_buy,
            "npv_rent": npv_rent,
            "details": {
                "P_future": P_future,
                "monthly_cost_own": Cost_own,
                "monthly_cost_rent": Cost_rent,
                "monthly_income_invest": Income_invest
            }
        }

    def decide(self, inputs: HousingDecisionInputs) -> str:
        """
        Executes the decision logic.
        Returns "BUY" or "RENT".
        """
        # 1. Safety Guardrail (DTI)
        # loan_amount = inputs.market_price * 0.8
        # annual_mortgage_cost = loan_amount * inputs.interest_rate
        # if annual_mortgage_cost > inputs.income * 0.4: return "RENT"

        loan_amount = inputs.market_price * 0.8
        annual_mortgage_cost = loan_amount * inputs.risk_free_rate
        dti_threshold = inputs.annual_income * 0.4

        if annual_mortgage_cost > dti_threshold:
            logger.debug(f"SYSTEM2_HOUSING | Force RENT due to DTI. Cost: {annual_mortgage_cost:.2f} > Limit: {dti_threshold:.2f}")
            return "RENT"

        # 2. Rational Choice
        results = self.calculate_housing_npv(inputs)
        npv_buy = results["npv_buy"]
        npv_rent = results["npv_rent"]

        decision = "BUY" if npv_buy > npv_rent else "RENT"

        logger.debug(
            f"SYSTEM2_HOUSING | Decision: {decision}. NPV_Buy: {npv_buy:.2f}, NPV_Rent: {npv_rent:.2f}. "
            f"Price: {inputs.market_price}, Future: {results['details']['P_future']:.2f}"
        )

        return decision

    def _detect_market_trend(self, price_history: deque) -> MarketTrend:
        """
        Detects market trend based on price history.
        Uses Option C: Trend Reversal Detection.
        """
        if len(price_history) < 3:
            return MarketTrend.FLAT

        prices = list(price_history)
        recent_prices = prices[-3:] # Last 3 points: t-2, t-1, t

        p0, p1, p2 = recent_prices[0], recent_prices[1], recent_prices[2]

        # Simple slope check
        delta1 = p1 - p0
        delta2 = p2 - p1

        # PEAK Detection: Rising then Falling
        if delta1 > 0 and delta2 < 0:
            return MarketTrend.FALLING # Reversal started

        # Continued Fall
        if delta1 < 0 and delta2 < 0:
            return MarketTrend.FALLING

        # Rising
        if delta1 > 0 and delta2 > 0:
            return MarketTrend.RISING

        return MarketTrend.FLAT

    def decide_selling(self, agent: Any, market_data: Dict[str, Any], current_tick: int) -> Optional[Tuple[str, int, float]]:
        """
        Decides whether to sell a property.
        Returns None or Tuple(Action="SELL", unit_id, target_price).
        """
        if not agent.owned_properties:
            return None

        # 1. Data Preparation
        housing_market = market_data.get("housing_market", {})
        market_price = housing_market.get("avg_sale_price")
        if not market_price:
            market_rent = housing_market.get("avg_rent_price", 100.0)
            market_price = market_rent * 12 * 20.0

        market_trend = self._detect_market_trend(agent.housing_price_history)

        # 2. Trigger 1: Distress Sale (Survival Crisis)
        # Condition: Cash < 2 months survival cost
        food_price = 5.0 # Fallback
        goods_market = market_data.get("goods_market", {})
        if "basic_food_current_sell_price" in goods_market:
            food_price = goods_market["basic_food_current_sell_price"]

        daily_survival_cost = food_price * getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
        monthly_survival_cost = daily_survival_cost * 30

        if agent.assets < (monthly_survival_cost * 2):
            # Sell immediately!
            # Pick a unit (e.g., the most valuable or random? Currently units are identical in estimated_value)
            # We pick the first one.
            unit_id = agent.owned_properties[0]

            # Distress Price: 95% of market price to sell fast
            target_price = market_price * 0.95

            logger.info(
                f"SYSTEM2_SELLING | DISTRESS SALE for Agent {agent.id}. Assets: {agent.assets:.2f} < Threshold {monthly_survival_cost*2:.2f}",
                extra={"tick": current_tick, "agent_id": agent.id}
            )
            return ("SELL", unit_id, target_price)

        # 3. Trigger 2: Profit Taking (Investment)
        # Condition: Price > Purchase * Target AND Trend is PEAK/FALLING
        target_return = getattr(self.config, "REAL_ESTATE_PROFIT_TARGET", 0.2) # 20% profit target

        if market_trend == MarketTrend.FALLING:
            # Check if any property meets profit target
            for unit_id in agent.owned_properties:
                purchase_price = agent.property_purchase_prices.get(unit_id, market_price) # Default to market if unknown

                # Avoid selling if we just bought it (same tick or very recent)
                # But here we just check price
                if market_price > purchase_price * (1.0 + target_return):
                    # System 2 Double Check: Is Selling + Renting better than Holding?
                    # We run NPV check for Renting vs Buying (Holding is equivalent to Buying/Keeping)

                    # Prepare Inputs for NPV
                    loan_market = market_data.get("loan_market", {})
                    risk_free_rate = loan_market.get("interest_rate", 0.05)
                    price_growth = 0.0 # Expecting 0 or negative since trend is falling

                    income = agent.current_wage * 100 if agent.is_employed else agent.expected_wage * 100
                    market_rent = housing_market.get("avg_rent_price", 100.0)

                    inputs = HousingDecisionInputs(
                        current_wealth=agent.assets + market_price, # Wealth after sell
                        annual_income=income,
                        market_rent_monthly=market_rent,
                        market_price=market_price,
                        risk_free_rate=risk_free_rate,
                        price_growth_expectation=price_growth # Pessimistic view
                    )

                    results = self.calculate_housing_npv(inputs)
                    # If Rent NPV > Buy NPV, it means we should not own. So Sell.
                    if results["npv_rent"] > results["npv_buy"]:
                        logger.info(
                            f"SYSTEM2_SELLING | PROFIT TAKING for Agent {agent.id}. Unit {unit_id}. "
                            f"Price {market_price:.0f} > Buy {purchase_price:.0f} (+{target_return:.0%}). Trend: {market_trend.name}",
                            extra={"tick": current_tick, "agent_id": agent.id}
                        )
                        return ("SELL", unit_id, market_price) # Sell at market price

        return None
