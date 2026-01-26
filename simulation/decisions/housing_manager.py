from __future__ import annotations
from typing import Any, Dict, Optional, TYPE_CHECKING, Union
import math
from simulation.models import Order

if TYPE_CHECKING:
    from modules.household.dtos import HouseholdStateDTO
    from simulation.dtos import HouseholdConfigDTO

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
    Refactored for DTO Purity Gate.
    """

    def __init__(self, agent: "HouseholdStateDTO", config: Union[Any, HouseholdConfigDTO]):
        self.agent = agent  # HouseholdStateDTO
        self.config = config

    def get_housing_tier(self, agent: "HouseholdStateDTO") -> float:
        """
        Estimates housing tier based on residence value.
        """
        if agent.is_homeless or agent.residing_property_id is None:
            return 0.0
        return 1.0 # Default Tier 1

    def decide_mimicry_purchase(self, reference_standard: Dict[str, float]) -> Optional[PurchaseIntent]:
        """
        Phase 17-4: Mimicry Consumption Logic.
        """
        # Use DTO attribute if available, otherwise legacy getattr
        enable_vanity = self.config.enable_vanity_system if hasattr(self.config, 'enable_vanity_system') else getattr(self.config, "ENABLE_VANITY_SYSTEM", False)

        if not enable_vanity:
            return None

        # 1. Calculate Gap
        my_tier = self.get_housing_tier(self.agent)
        ref_tier = reference_standard.get("avg_housing_tier", 1.0)

        gap = ref_tier - my_tier
        if gap <= 0:
            return None

        # 2. Calculate Urgency
        conformity = getattr(self.agent, "conformity", 0.5)

        mimicry_factor = self.config.mimicry_factor if hasattr(self.config, 'mimicry_factor') else getattr(self.config, "MIMICRY_FACTOR", 0.5)

        urgency = conformity * gap * mimicry_factor

        # 3. Trigger Condition
        if urgency > 0.5:
             return PurchaseIntent(
                 target="housing",
                 max_ltv=0.95, # Panic Buy: Max Leverage
                 priority="URGENT"
             )
        return None

    def should_buy(self, property_value: float, rent_price: float, interest_rate: float = 0.05) -> bool:
        """
        Determines whether to buy a property based on NPV calculation biased by personality.
        """
        # 1. Base Economic Parameters
        horizon = 120
        discount_rate = 0.005
        maintenance_rate = self.config.maintenance_rate_per_tick if hasattr(self.config, 'maintenance_rate_per_tick') else self.config.MAINTENANCE_RATE_PER_TICK
        
        # 2. Personality-Biased Parameters
        
        # Optimism Bias
        base_appreciation = 0.002
        perceived_appreciation_rate = base_appreciation * (0.5 + getattr(self.agent, 'optimism', 0.5))
        
        # Ambition Bias
        prestige_bonus = 0.0
        ambition = getattr(self.agent, 'ambition', 0.5)
        prestige_bonus = property_value * 0.1 * ambition

        # 3. NPV Calculation
        rent_npv = 0.0
        for t in range(horizon):
            rent_npv += rent_price / ((1 + discount_rate) ** t)
            
        ltv = 0.8
        down_payment = property_value * (1 - ltv)
        loan_principal = property_value * ltv
        
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
        net_buy_cost = buy_outflow_npv - future_value_npv - prestige_bonus
        
        return net_buy_cost < rent_npv
