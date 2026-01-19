from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class StressScenarioConfig:
    """
    Data Transfer Object for configuring and passing stress scenario parameters through the simulation.
    This centralized DTO prevents pollution of the global config module and ensures explicit data flow.
    """
    # General Scenario Flags
    is_active: bool = False
    scenario_name: Optional[str] = None
    start_tick: int = 0

    # --- Scenario 1: Hyperinflation Parameters ---
    # Multiplies household adaptation_rate to speed up reaction to price changes.
    inflation_expectation_multiplier: float = 1.0

    # Extra percentage of goods to buy when expected inflation is high (e.g., 0.1 = 10% more).
    hoarding_propensity_factor: float = 0.0

    # One-time cash injection as a percentage of current assets (e.g., 0.5 = 50% increase).
    demand_shock_cash_injection: float = 0.0


    # --- Scenario 2: Deflationary Spiral Parameters ---
    # Enables asset fire-sales by agents if their financial situation is dire.
    panic_selling_enabled: bool = False

    # Multiplies the agent's desire to repay debt versus consuming or investing.
    debt_aversion_multiplier: float = 1.0

    # Percentage reduction in consumption if the agent is pessimistic (e.g., unemployed). (0.2 = 20% reduction)
    consumption_pessimism_factor: float = 0.0

    # One-time asset reduction as a percentage (e.g., 0.5 = 50% reduction).
    asset_shock_reduction: float = 0.0


    # --- Scenario 3: Supply Shock Parameters ---
    # Dictionary mapping firm types or specific goods to a productivity multiplier (e.g., {"Farm": 0.5}).
    exogenous_productivity_shock: Dict[str, float] = field(default_factory=dict)

    # --- Scenario 4: Great Depression (Liquidity Crisis) ---
    # Target base rate for the Central Bank (e.g., 0.08)
    monetary_shock_target_rate: Optional[float] = None

    # Target corporate tax rate for the Government (e.g., 0.30)
    fiscal_shock_tax_rate: Optional[float] = None
