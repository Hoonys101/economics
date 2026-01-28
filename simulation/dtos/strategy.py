from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ScenarioStrategy:
    """
    Unified Configuration DTO for Simulation Scenarios.
    Replaces StressScenarioConfig and eliminates global config pollution.
    """
    # General Scenario Flags
    name: str = "Default"
    is_active: bool = False
    start_tick: int = 0
    scenario_name: Optional[str] = None # Kept for backward compatibility with StressScenarioConfig

    # --- Phase 28: Stress Testing Parameters ---
    inflation_expectation_multiplier: float = 1.0
    hoarding_propensity_factor: float = 0.0
    demand_shock_cash_injection: float = 0.0
    panic_selling_enabled: bool = False
    debt_aversion_multiplier: float = 1.0
    consumption_pessimism_factor: float = 0.0
    asset_shock_reduction: float = 0.0
    exogenous_productivity_shock: Dict[str, float] = field(default_factory=dict)

    # Scenario 4: Great Depression
    monetary_shock_target_rate: Optional[float] = None
    fiscal_shock_tax_rate: Optional[float] = None
    base_interest_rate_multiplier: Optional[float] = None
    corporate_tax_rate_delta: Optional[float] = None
    demand_shock_multiplier: Optional[float] = None

    # --- Phase 23: Industrial Revolution Parameters ---
    # Formerly injected via setattr into config
    tfp_multiplier: float = 3.0 # Maps to TECH_FERTILIZER_MULTIPLIER. Default 3.0 matches legacy default.
    tech_fertilizer_unlock_tick: int = 50
    tech_diffusion_rate: float = 0.05
    food_sector_config: Dict[str, Any] = field(default_factory=dict)
    market_config: Dict[str, Any] = field(default_factory=dict)
    deflationary_pressure_multiplier: float = 1.0
    limits: Dict[str, Any] = field(default_factory=dict)
    firm_decision_engine: Optional[str] = None
    household_decision_engine: Optional[str] = None

    # Generic
    parameters: Dict[str, Any] = field(default_factory=dict) # Catch-all for unmapped params if any
