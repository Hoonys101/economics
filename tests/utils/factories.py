from unittest.mock import MagicMock
from typing import Optional
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.models import Talent
from simulation.ai.api import Personality
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine
from simulation.dtos.config_dtos import HouseholdConfigDTO, FirmConfigDTO
from modules.system.api import DEFAULT_CURRENCY

def create_household_config_dto(**kwargs) -> HouseholdConfigDTO:
    defaults = {
        "survival_need_consumption_threshold": 50.0,
        "target_food_buffer_quantity": 2.0,
        "food_purchase_max_per_tick": 10.0,
        "assets_threshold_for_other_actions": 100.0,
        "wage_decay_rate": 0.01,
        "reservation_wage_floor": 5.0,
        "survival_critical_turns": 10.0,
        "labor_market_min_wage": 7.0,
        "household_low_asset_threshold": 50.0,
        "household_low_asset_wage": 7.0,
        "household_default_wage": 10.0,
        "market_price_fallback": 10.0,
        "need_factor_base": 1.0,
        "need_factor_scale": 1.0,
        "valuation_modifier_base": 1.0,
        "valuation_modifier_range": 0.2,
        "household_max_purchase_quantity": 20.0,
        "bulk_buy_need_threshold": 80.0,
        "bulk_buy_agg_threshold": 0.8,
        "bulk_buy_moderate_ratio": 0.5,
        "panic_buying_threshold": 0.9,
        "hoarding_factor": 1.5,
        "deflation_wait_threshold": -0.01,
        "delay_factor": 0.5,
        "dsr_critical_threshold": 0.4,
        "budget_limit_normal_ratio": 0.5,
        "budget_limit_urgent_need": 100.0,
        "budget_limit_urgent_ratio": 0.9,
        "min_purchase_quantity": 1.0,
        "job_quit_threshold_base": 0.5,
        "job_quit_prob_base": 0.1,
        "job_quit_prob_scale": 0.1,
        "stock_market_enabled": True,
        "household_min_assets_for_investment": 500.0,
        "stock_investment_equity_delta_threshold": 0.1,
        "stock_investment_diversification_count": 3,
        "expected_startup_roi": 0.2,
        "startup_cost": 1000.0,
        "debt_repayment_ratio": 0.1,
        "debt_repayment_cap": 0.5,
        "debt_liquidity_ratio": 0.2,
        "initial_rent_price": 500.0,
        "default_mortgage_rate": 0.05,
        "enable_vanity_system": True,
        "mimicry_factor": 0.1,
        "maintenance_rate_per_tick": 0.001,
        "goods": {"food": {}, "basic_food": {}, "luxury_food": {}},
        "household_consumable_goods": ["food", "basic_food", "luxury_food"],
        "value_orientation_mapping": {},
        "price_memory_length": 10,
        "wage_memory_length": 10,
        "ticks_per_year": 365,
        "adaptation_rate_normal": 0.1,
        "adaptation_rate_impulsive": 0.2,
        "adaptation_rate_conservative": 0.05,
        "conformity_ranges": {},
        "initial_household_assets_mean": 1000.0,
        "quality_pref_snob_min": 0.8,
        "quality_pref_miser_max": 0.2,
        "wage_recovery_rate": 0.1,
        "learning_efficiency": 0.5,
        "default_fallback_price": 10.0,
        "need_medium_threshold": 50.0,
        "housing_expectation_cap": 1000.0,
        "household_min_wage_demand": 7.0,
        "panic_selling_asset_threshold": 100.0,
        "perceived_price_update_factor": 0.1,
        "social_status_asset_weight": 0.5,
        "social_status_luxury_weight": 0.5,
        "leisure_coeffs": {},
        "base_desire_growth": 0.1,
        "max_desire_value": 100.0,
        "survival_need_death_threshold": 100.0,
        "assets_death_threshold": -100.0,
        "household_death_turns_threshold": 10,
        "survival_need_death_ticks_threshold": 10.0,
        "initial_wage": 10.0,
        "education_cost_multipliers": {},
        "survival_need_emergency_threshold": 80.0,
        "primary_survival_good_id": "food",
        "survival_bid_premium": 0.2,
        "elasticity_mapping": {"DEFAULT": 1.0},
        "max_willingness_to_pay_multiplier": 1.5,
        "initial_household_age_range": (20.0, 60.0),
        "initial_aptitude_distribution": (0.5, 0.15),
        "emergency_liquidation_discount": 0.8,
        "emergency_stock_liquidation_fallback_price": 8.0,
        "distress_grace_period_ticks": 5,
        "ai_epsilon_decay_params": (0.5, 0.05, 700),
        "housing_npv_horizon_years": 10,
        "housing_npv_risk_premium": 0.02,
        "mortgage_default_down_payment_rate": 0.2,
        "age_death_probabilities": {60: 0.01, 70: 0.02, 80: 0.05, 90: 0.15, 100: 0.50},
        "fallback_survival_cost": 10.0,
        "base_labor_skill": 1.0,
    }
    defaults.update(kwargs)
    return HouseholdConfigDTO(**defaults)

def create_firm_config_dto(**kwargs) -> FirmConfigDTO:
    defaults = {
        "firm_min_production_target": 10.0,
        "firm_max_production_target": 100.0,
        "startup_cost": 1000.0,
        "seo_trigger_ratio": 2.0,
        "seo_max_sell_ratio": 0.5,
        "automation_cost_per_pct": 100.0,
        "firm_safety_margin": 0.2,
        "automation_tax_rate": 0.1,
        "altman_z_score_threshold": 1.8,
        "dividend_suspension_loss_ticks": 5,
        "dividend_rate": 0.05,
        "dividend_rate_min": 0.0,
        "dividend_rate_max": 0.1,
        "labor_alpha": 0.6,
        "automation_labor_reduction": 0.5,
        "severance_pay_weeks": 4.0,
        "labor_market_min_wage": 7.0,
        "overstock_threshold": 2.0,
        "understock_threshold": 0.5,
        "production_adjustment_factor": 0.1,
        "max_sell_quantity": 100.0,
        "invisible_hand_sensitivity": 0.1,
        "capital_to_output_ratio": 2.0,
        "initial_base_annual_rate": 0.05,
        "default_loan_spread": 0.02,
        "initial_firm_liquidity_need": 500.0,
        "bankruptcy_consecutive_loss_threshold": 10,
        "profit_history_ticks": 10,
        "ipo_initial_shares": 1000.0,
        "inventory_holding_cost_rate": 0.01,
        "firm_maintenance_fee": 10.0,
        "corporate_tax_rate": 0.2,
        "bailout_repayment_ratio": 0.1,
        "valuation_per_multiplier": 10.0,
        "capital_depreciation_rate": 0.05,
        "labor_elasticity_min": 0.5,
        "goods": {"food": {}, "basic_food": {}, "luxury_food": {}},
        "halo_effect": 0.1,
        "marketing_decay_rate": 0.1,
        "marketing_efficiency": 1.0,
        "perceived_quality_alpha": 0.5,
        "brand_awareness_saturation": 100.0,
        "marketing_efficiency_high_threshold": 0.8,
        "marketing_efficiency_low_threshold": 0.2,
        "marketing_budget_rate_min": 0.01,
        "marketing_budget_rate_max": 0.1,
        "brand_resilience_factor": 0.1,
        "default_target_margin": 0.2,
        "max_price_staleness_ticks": 5,
        "fire_sale_asset_threshold": 100.0,
        "fire_sale_inventory_threshold": 50.0,
        "fire_sale_inventory_target": 10.0,
        "fire_sale_discount": 0.5,
        "fire_sale_cost_discount": 0.8,
        "sale_timeout_ticks": 10,
        "dynamic_price_reduction_factor": 0.05,
        "ai_epsilon_decay_params": (0.5, 0.05, 700),
        "ai_reward_brand_value_multiplier": 0.05,
    }
    defaults.update(kwargs)
    return FirmConfigDTO(**defaults)

def create_household(
    config_dto: HouseholdConfigDTO = None,
    id: int = 1,
    name: str = "TestHousehold",
    assets: float = 1000.0,
    initial_needs: dict = None,
    value_orientation: str = "needs_and_social_status",
    engine: Optional[IDecisionEngine] = None,
    **kwargs
) -> Household:
    if config_dto is None:
        config_dto = create_household_config_dto()

    if initial_needs is None:
        initial_needs = config_dto.initial_needs.copy()

    core_config = AgentCoreConfigDTO(
        id=id,
        name=name,
        initial_needs=initial_needs,
        logger=MagicMock(),
        memory_interface=None,
        value_orientation=value_orientation
    )

    if engine is None:
        engine = MagicMock()

    talent = kwargs.pop('talent', Talent(base_learning_rate=0.5, max_potential={}))
    goods_data = kwargs.pop('goods_data', [{"id": "food", "initial_price": 10.0}])
    personality = kwargs.pop('personality', Personality.CONSERVATIVE)

    # Cast assets to int for consistency
    assets_pennies = int(assets)

    household = Household(
        core_config=core_config,
        engine=engine,
        talent=talent,
        goods_data=goods_data,
        personality=personality,
        config_dto=config_dto,
        initial_assets_record=assets_pennies,
        **kwargs
    )
    if assets_pennies > 0:
        household.deposit(assets_pennies, DEFAULT_CURRENCY)
    return household

def create_firm(
    config_dto: FirmConfigDTO = None,
    id: int = 100,
    name: str = "TestFirm",
    assets: float = 10000.0,
    specialization: str = "food",
    productivity_factor: float = 1.0,
    initial_needs: dict = None,
    value_orientation: str = "PROFIT",
    engine: Optional[IDecisionEngine] = None,
    **kwargs
) -> Firm:
    if config_dto is None:
        config_dto = create_firm_config_dto()

    if initial_needs is None:
        initial_needs = {}

    core_config = AgentCoreConfigDTO(
        id=id,
        name=name,
        initial_needs=initial_needs,
        logger=MagicMock(),
        memory_interface=None,
        value_orientation=value_orientation
    )

    if engine is None:
        engine = MagicMock()

    firm = Firm(
        core_config=core_config,
        engine=engine,
        specialization=specialization,
        productivity_factor=productivity_factor,
        config_dto=config_dto,
        initial_inventory=kwargs.get("initial_inventory"),
        loan_market=kwargs.get("loan_market"),
        sector=kwargs.get("sector", "FOOD"),
        personality=kwargs.get("personality")
    )

    assets_pennies = int(assets)
    if assets_pennies > 0:
        firm.deposit(assets_pennies, DEFAULT_CURRENCY)

    return firm
