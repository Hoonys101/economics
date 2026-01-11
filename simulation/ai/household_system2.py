from typing import Any, Dict, Optional, NamedTuple
import math
import logging

logger = logging.getLogger(__name__)

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

    def decide_selling(self, market_data: Dict[str, Any], current_time: int) -> Optional[str]:
        """
        WO-050: Determines if the agent should sell their property.
        Returns "SELL_DISTRESS", "SELL_PROFIT", or None.
        """
        # 1. Check if agent owns properties
        owned_properties = getattr(self.agent, 'owned_properties', [])
        if not owned_properties:
            return None

        # 2. Calculate Distress Threshold
        goods_market = market_data.get("goods_market", {})
        # Note: 'basic_food_avg_traded_price' is more stable than 'current_sell_price'
        food_price = goods_market.get("basic_food_avg_traded_price", 5.0)
        daily_food_consumption = getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        monthly_survival_cost = daily_food_consumption * food_price * 30.0
        distress_threshold = monthly_survival_cost * 1.5

        # 3. Distress Check
        if self.agent.assets < distress_threshold:
            logger.info(f"DISTRESS_SELL | Agent {self.agent.id} triggered distress sale.")
            return "SELL_DISTRESS"

        # 4. Profit Check (Placeholder)
        # if market_price > last_purchase_price * 1.2: return "SELL_PROFIT"

        return None
