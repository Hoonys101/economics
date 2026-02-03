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
        T_years = getattr(self.config, "HOUSING_NPV_HORIZON_YEARS", 10)
        T_months = T_years * 12

        # Monthly Discount Rate
        # r = (interest_rate + risk_premium) / 12
        risk_premium = getattr(self.config, "HOUSING_NPV_RISK_PREMIUM", 0.02)
        r_monthly = (inputs.risk_free_rate + risk_premium) / 12.0

        # Buying Components
        P_initial = inputs.market_price
        U_shelter = inputs.market_rent_monthly
        maintenance_rate = getattr(self.config, "HOUSING_ANNUAL_MAINTENANCE_RATE", 0.01)
        Cost_own = (P_initial * maintenance_rate) / 12.0

        # Price Growth Expectation (Capped at 5%)
        g_annual = min(inputs.price_growth_expectation, getattr(self.config, "HOUSING_EXPECTATION_CAP", 0.05))
        P_future = P_initial * ((1.0 + g_annual) ** T_years)

        # Renting Components
        # Principal = Down Payment
        down_payment_rate = getattr(self.config, "MORTGAGE_DEFAULT_DOWN_PAYMENT_RATE", 0.2)
        Principal = P_initial * down_payment_rate
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
