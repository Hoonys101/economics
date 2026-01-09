from typing import Any, Dict, Optional
import math
from simulation.models import Order # Type hint purpose mostly

class PurchaseIntent:
    """DTO for Mimicry Purchase decision"""
    def __init__(self, target="housing", max_ltv=0.8, priority="NORMAL"):
        self.target = target
        self.max_ltv = max_ltv
        self.priority = priority

class HousingManager:
    """
    Phase 17-3B: Housing Manager
    Acts as a 'Proxy Planner' (System 2 Proxy) for the Household.
    Calculates Buy vs Rent decisions using NPV and Personality Bias.
    """

    def __init__(self, agent: Any, config: Any):
        self.agent = agent  # Household instance
        self.config = config

    def get_housing_tier(self, agent: Any) -> float:
        """
        Estimates housing tier based on residence value.
        Tier 1 ~ 10000 (Basic), Tier 3 ~ 30000 (High)
        Returns a float score (e.g. 1.0, 3.0)
        """
        # If agent owns/rents, we need the property value.
        # Currently agent stores `residing_property_id`.
        # Accessing `agent.decision_engine.market_data` or passing context is hard here.
        # Ideally, we pass property_value.
        # As a heuristic, if homeless, 0.0. If has home, assume standard (1.0) or check value if possible.
        # Since we don't have easy access to RealEstateUnit here without passing it,
        # we will assume standard Tier 1 (1.0) if not homeless, 0.0 if homeless.
        # For verification, we might need to inject this.
        if agent.is_homeless or agent.residing_property_id is None:
            return 0.0
        return 1.0 # Default Tier 1

    def decide_mimicry_purchase(self, reference_standard: Dict[str, float]) -> Optional[PurchaseIntent]:
        """
        Phase 17-4: Mimicry Consumption Logic.
        If Relative Deprivation > Threshold, trigger Panic Buy.
        """
        if not getattr(self.config, "ENABLE_VANITY_SYSTEM", False):
            return None

        # 1. Calculate Gap
        # Note: referencing self.agent inside helper
        my_tier = self.get_housing_tier(self.agent)
        ref_tier = reference_standard.get("avg_housing_tier", 1.0)

        gap = ref_tier - my_tier
        if gap <= 0:
            return None # Already at or above reference

        # 2. Calculate Urgency
        # urgency = Conformity * Gap * MimicryFactor
        conformity = getattr(self.agent, "conformity", 0.5)
        mimicry_factor = getattr(self.config, "MIMICRY_FACTOR", 0.5)

        urgency = conformity * gap * mimicry_factor

        # 3. Trigger Condition
        if urgency > 0.5: # Threshold
             return PurchaseIntent(
                 target="housing",
                 max_ltv=0.95, # Panic Buy: Max Leverage
                 priority="URGENT"
             )
        return None

    def should_buy(self, property_value: float, rent_price: float, interest_rate: float = 0.05) -> bool:
        """
        Determines whether to buy a property based on NPV calculation biased by personality.
        
        Args:
            property_value: Asking price of the property.
            rent_price: Current or expected monthly rent.
            interest_rate: Annual mortgage interest rate (approximate).

        Returns:
            True if the agent should buy, False otherwise.
        """
        # 1. Base Economic Parameters
        horizon = 120  # 10 years (120 ticks) horizon for calculation
        discount_rate = 0.005 # 0.5% per tick discount rate
        maintenance_rate = self.config.MAINTENANCE_RATE_PER_TICK # 0.1%
        
        # 2. Personality-Biased Parameters
        
        # Optimism Bias: Optimists over-estimate future appreciation
        # Base appreciation 0.2% per tick. Optimist (1.0) sees 0.4%, Pessimist (0.0) sees 0.0%
        base_appreciation = 0.002
        perceived_appreciation_rate = base_appreciation * (0.5 + self.agent.optimism)
        
        # Ambition Bias: Ambitious agents perceive "Prestige Value" as tangible benefit
        # Ambition 1.0 adds 10% of property value to total utility
        prestige_bonus = 0.0
        if hasattr(self.agent, 'ambition'):
             prestige_bonus = property_value * 0.1 * self.agent.ambition

        # 3. NPV Calculation
        
        # Cost of Renting (Outflow)
        rent_npv = 0.0
        for t in range(horizon):
            rent_npv += rent_price / ((1 + discount_rate) ** t)
            
        # Cost of Buying (Outflow - Inflow)
        # Outflows: Down Payment, Mortgage Pmt, Maintenance
        # Inflow: Asset Value at horizon (Appreciated)
        
        ltv = 0.8
        down_payment = property_value * (1 - ltv)
        loan_principal = property_value * ltv
        
        # Mortgage Payment (Simplified Amortization for calc)
        # Monthly Rate = Interest Rate / 12 (approx, since ticks are months)
        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            monthly_payment = loan_principal * (monthly_rate * (1 + monthly_rate) ** 360) / ((1 + monthly_rate) ** 360 - 1)
        else:
            monthly_payment = loan_principal / 360
            
        buy_outflow_npv = down_payment
        for t in range(horizon):
            maintenance_cost = property_value * maintenance_rate
            total_monthly_cost = monthly_payment + maintenance_cost
            buy_outflow_npv += total_monthly_cost / ((1 + discount_rate) ** t)
            
        future_value = property_value * ((1 + perceived_appreciation_rate) ** horizon)
        future_value_npv = future_value / ((1 + discount_rate) ** horizon)
        
        # Net Cost of Buying (Cost - Asset Value - Prestige)
        # Note: We compare Costs. Lower is better.
        # So we treat Gain as Negative Cost.
        
        net_buy_cost = buy_outflow_npv - future_value_npv - prestige_bonus
        
        # 4. Decision
        # If Buying is cheaper (or has more utility) than Renting
        return net_buy_cost < rent_npv
