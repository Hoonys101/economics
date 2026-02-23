from dataclasses import dataclass, field
from modules.common.enums import IndustryDomain as IndustryDomain
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Any, Protocol

class IFirmStateProvider(Protocol):
    """
    Protocol for entities that can provide their state as a FirmStateDTO.
    Replaces the legacy 'from_firm' factory probing.
    """
    def get_state_dto(self) -> FirmStateDTO:
        """Returns the immutable state DTO of the firm."""

@dataclass(frozen=True)
class FinanceStateDTO:
    """Composite state for Finance Department."""
    balance: int
    revenue_this_turn: int
    expenses_this_tick: int
    consecutive_loss_turns: int
    profit_history: list[int]
    altman_z_score: float
    valuation: int
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    is_publicly_traded: bool
    total_debt_pennies: int = ...
    average_interest_rate: float = ...

@dataclass(frozen=True)
class ProductionStateDTO:
    """Composite state for Production Department."""
    current_production: float
    productivity_factor: float
    production_target: float
    capital_stock: float
    base_quality: float
    automation_level: float
    specialization: str
    inventory: dict[str, Any]
    input_inventory: dict[str, Any]
    inventory_quality: dict[str, float]
    major: IndustryDomain = ...
    physical_quality: float = ...
    brand_prestige: float = ...

@dataclass(frozen=True)
class SalesStateDTO:
    """Composite state for Sales Department."""
    inventory_last_sale_tick: dict[str, int]
    price_history: dict[str, int]
    brand_awareness: float
    perceived_quality: float
    marketing_budget: int
    marketing_budget_rate: float = ...
    adstock: float = ...

@dataclass(frozen=True)
class HRStateDTO:
    """Composite state for HR Department."""
    employees: list[str]
    employees_data: dict[str, dict[str, Any]]
    hires_prev_tick: int = ...
    target_hires_prev_tick: int = ...
    wage_offer_prev_tick: int = ...

@dataclass(frozen=True)
class FirmStateDTO:
    """
    A read-only DTO containing the state of a Firm agent.
    Used by DecisionEngines to make decisions without direct dependency on the Firm class.
    """
    id: int
    is_active: bool
    finance: FinanceStateDTO
    production: ProductionStateDTO
    sales: SalesStateDTO
    hr: HRStateDTO
    agent_data: dict[str, Any]
    system2_guidance: dict[str, Any]
    sentiment_index: float
    market_insight: float = ...
    @classmethod
    def from_provider(cls, provider: IFirmStateProvider) -> FirmStateDTO:
        """
        Creates a FirmStateDTO from an IFirmStateProvider.
        Strictly enforces the Protocol.
        """

@dataclass
class HouseholdConfigDTO:
    """
    Static configuration values relevant to household decisions.
    All monetary values are in Integer Pennies.
    """
    startup_cost: int
    labor_market_min_wage: int
    household_low_asset_wage: int
    household_default_wage: int
    initial_rent_price: int
    initial_wage: int
    emergency_stock_liquidation_fallback_price: int
    fallback_survival_cost: int
    default_food_price_estimate: int
    household_min_wage_demand: int
    initial_household_assets_mean: int
    survival_bid_premium: int
    household_min_assets_for_investment: int
    survival_need_consumption_threshold: float
    target_food_buffer_quantity: float
    food_purchase_max_per_tick: float
    assets_threshold_for_other_actions: int
    wage_decay_rate: float
    reservation_wage_floor: float
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
    stock_investment_equity_delta_threshold: float
    stock_investment_diversification_count: int
    expected_startup_roi: float
    debt_repayment_ratio: float
    debt_repayment_cap: float
    debt_liquidity_ratio: float
    default_mortgage_rate: float
    enable_vanity_system: bool
    mimicry_factor: float
    maintenance_rate_per_tick: float
    housing_expectation_cap: float
    housing_npv_horizon_years: int
    housing_npv_risk_premium: float
    mortgage_default_down_payment_rate: float
    goods: dict[str, Any]
    household_consumable_goods: list[str]
    value_orientation_mapping: dict[str, Any]
    price_memory_length: int
    wage_memory_length: int
    ticks_per_year: int
    adaptation_rate_normal: float
    adaptation_rate_impulsive: float
    adaptation_rate_conservative: float
    conformity_ranges: dict[str, Any]
    quality_pref_snob_min: float
    quality_pref_miser_max: float
    wage_recovery_rate: float
    learning_efficiency: float
    default_fallback_price: int
    need_medium_threshold: float
    panic_selling_asset_threshold: int
    perceived_price_update_factor: float
    social_status_asset_weight: float
    social_status_luxury_weight: float
    leisure_coeffs: dict[str, Any]
    base_desire_growth: float
    max_desire_value: float
    survival_need_death_threshold: float
    assets_death_threshold: float
    household_death_turns_threshold: float
    survival_need_death_ticks_threshold: float
    education_cost_multipliers: dict[int, float]
    survival_need_emergency_threshold: float
    primary_survival_good_id: str
    elasticity_mapping: dict[str, float]
    max_willingness_to_pay_multiplier: float
    initial_household_age_range: tuple[float, float]
    initial_aptitude_distribution: tuple[float, float]
    emergency_liquidation_discount: float
    distress_grace_period_ticks: int
    ai_epsilon_decay_params: tuple[float, float, int]
    age_death_probabilities: dict[int, float]
    base_labor_skill: float
    survival_budget_allocation: float
    food_consumption_utility: float
    survival_critical_turns: float
    household_low_asset_threshold: int
    insight_decay_rate: float
    insight_learning_multiplier: float
    education_boost_amount: float
    insight_threshold_realtime: float
    insight_threshold_sma: float
    panic_trigger_threshold: float
    debt_noise_factor: float
    panic_consumption_dampener: float
    labor_market: dict[str, Any] = field(default_factory=dict)

@dataclass
class FirmConfigDTO:
    """
    Static configuration values relevant to firm decisions.
    All monetary values are in Integer Pennies.
    """
    startup_cost: int
    labor_market_min_wage: int
    default_unit_cost: int
    automation_cost_per_pct: int
    firm_maintenance_fee: int
    firm_min_production_target: float
    firm_max_production_target: float
    seo_trigger_ratio: float
    seo_max_sell_ratio: float
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
    overstock_threshold: float
    understock_threshold: float
    production_adjustment_factor: float
    max_sell_quantity: float
    invisible_hand_sensitivity: float
    capital_to_output_ratio: float
    initial_base_annual_rate: float
    default_loan_spread: float
    initial_firm_liquidity_need: int
    bankruptcy_consecutive_loss_threshold: int
    profit_history_ticks: int
    ipo_initial_shares: float
    inventory_holding_cost_rate: float
    corporate_tax_rate: float
    bailout_repayment_ratio: float
    valuation_per_multiplier: float
    capital_depreciation_rate: float
    labor_elasticity_min: float
    goods: dict[str, Any]
    halo_effect: float
    marketing_decay_rate: float
    marketing_efficiency: float
    perceived_quality_alpha: float
    brand_awareness_saturation: float
    marketing_efficiency_high_threshold: float
    marketing_efficiency_low_threshold: float
    marketing_budget_rate_min: float
    marketing_budget_rate_max: float
    brand_resilience_factor: float
    default_target_margin: float
    max_price_staleness_ticks: int
    fire_sale_asset_threshold: float
    fire_sale_inventory_threshold: float
    fire_sale_inventory_target: float
    fire_sale_discount: float
    fire_sale_cost_discount: float
    sale_timeout_ticks: int
    dynamic_price_reduction_factor: float
    ai_epsilon_decay_params: tuple[float, float, int]
    ai_reward_brand_value_multiplier: float
    space_utility_factor: float
    labor_market: dict[str, Any] = field(default_factory=dict)
    identity_quality_ratio: float = ...

@dataclass
class ServerConfigDTO:
    """Configuration for system security and access control."""
    god_mode_token: str
    host: str = ...
    port: int = ...
