from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class HouseholdConfigDTO:
    """Static configuration values relevant to household decisions."""
    survival_need_consumption_threshold: float
    target_food_buffer_quantity: float
    food_purchase_max_per_tick: float
    assets_threshold_for_other_actions: float
    wage_decay_rate: float
    reservation_wage_floor: float
    survival_critical_turns: float
    labor_market_min_wage: float
    # New from Household.make_decision refactoring
    household_low_asset_threshold: float
    household_low_asset_wage: float
    household_default_wage: float

    # AI Engine requirements
    market_price_fallback: float
    need_factor_base: float
    need_factor_scale: float
    valuation_modifier_base: float
    valuation_modifier_range: float
    household_max_purchase_quantity: float
    bulk_buy_need_threshold: float
    bulk_buy_agg_threshold: float
    bulk_buy_moderate_ratio: float
    panic_buying_threshold: float
    hoarding_factor: float
    deflation_wait_threshold: float
    delay_factor: float
    dsr_critical_threshold: float
    budget_limit_normal_ratio: float
    budget_limit_urgent_need: float
    budget_limit_urgent_ratio: float
    min_purchase_quantity: float
    job_quit_threshold_base: float
    job_quit_prob_base: float
    job_quit_prob_scale: float
    stock_market_enabled: bool
    household_min_assets_for_investment: float
    stock_investment_equity_delta_threshold: float
    stock_investment_diversification_count: int
    expected_startup_roi: float
    startup_cost: float
    debt_repayment_ratio: float
    debt_repayment_cap: float
    debt_liquidity_ratio: float
    # Added for parity
    initial_rent_price: float
    # Added for AI Engine Purity
    default_mortgage_rate: float
    # Housing Manager
    enable_vanity_system: bool
    mimicry_factor: float
    maintenance_rate_per_tick: float
    goods: Dict[str, Any]
    household_consumable_goods: List[str]

    # Expanded Fields for DTO Parity
    value_orientation_mapping: Dict[str, Any]
    price_memory_length: int
    wage_memory_length: int
    ticks_per_year: int
    adaptation_rate_normal: float
    adaptation_rate_impulsive: float
    adaptation_rate_conservative: float
    conformity_ranges: Dict[str, Any]
    initial_household_assets_mean: float
    quality_pref_snob_min: float
    quality_pref_miser_max: float
    wage_recovery_rate: float
    learning_efficiency: float
    default_fallback_price: float
    need_medium_threshold: float
    housing_expectation_cap: float
    household_min_wage_demand: float
    panic_selling_asset_threshold: float
    perceived_price_update_factor: float
    social_status_asset_weight: float
    social_status_luxury_weight: float
    leisure_coeffs: Dict[str, Any]
    base_desire_growth: float
    max_desire_value: float
    survival_need_death_threshold: float
    assets_death_threshold: float
    household_death_turns_threshold: float
    initial_wage: float
    education_cost_multipliers: Dict[int, float]

    # Phase 2: Survival Override
    survival_need_emergency_threshold: float
    primary_survival_good_id: str
    survival_bid_premium: float

@dataclass
class FirmConfigDTO:
    """Static configuration values relevant to firm decisions."""
    firm_min_production_target: float
    firm_max_production_target: float
    startup_cost: float
    seo_trigger_ratio: float
    seo_max_sell_ratio: float
    automation_cost_per_pct: float
    firm_safety_margin: float
    automation_tax_rate: float
    altman_z_score_threshold: float
    dividend_suspension_loss_ticks: int
    dividend_rate: float
    dividend_rate_min: float
    dividend_rate_max: float
    labor_alpha: float
    automation_labor_reduction: float
    severance_pay_weeks: float
    labor_market_min_wage: float
    overstock_threshold: float
    understock_threshold: float
    production_adjustment_factor: float
    max_sell_quantity: float
    invisible_hand_sensitivity: float
    capital_to_output_ratio: float
    initial_base_annual_rate: float # WO-146 Fallback
    default_loan_spread: float      # WO-146 Configurable Spread

    # Expanded Fields for DTO Parity
    initial_firm_liquidity_need: float
    bankruptcy_consecutive_loss_threshold: int
    profit_history_ticks: int
    ipo_initial_shares: float
    inventory_holding_cost_rate: float
    firm_maintenance_fee: float
    corporate_tax_rate: float
    bailout_repayment_ratio: float
    valuation_per_multiplier: float
    capital_depreciation_rate: float
    labor_elasticity_min: float
    goods: Dict[str, Any]
    halo_effect: float
    marketing_decay_rate: float
    marketing_efficiency: float
    perceived_quality_alpha: float
    brand_awareness_saturation: float
    marketing_efficiency_high_threshold: float
    marketing_efficiency_low_threshold: float
    marketing_budget_rate_min: float
    marketing_budget_rate_max: float

    # Phase 2: Pricing Logic
    default_target_margin: float
    max_price_staleness_ticks: int
    fire_sale_asset_threshold: float
    fire_sale_inventory_threshold: float
    fire_sale_inventory_target: float
    fire_sale_discount: float
    fire_sale_cost_discount: float
