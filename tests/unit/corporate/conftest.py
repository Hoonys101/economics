import pytest
from unittest.mock import MagicMock
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from modules.simulation.dtos.api import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from tests.utils.factories import create_firm_config_dto

class MockConfig:
    CAPITAL_TO_OUTPUT_RATIO = 2.0
    DIVIDEND_RATE = 0.1
    DIVIDEND_RATE_MIN = 0.1
    DIVIDEND_RATE_MAX = 0.5
    MAX_SELL_QUANTITY = 100
    LABOR_MARKET_MIN_WAGE = 10.0
    GOODS = {"food": {"production_cost": 10.0, "inputs": {}}}
    AUTOMATION_COST_PER_PCT = 1000.0
    FIRM_SAFETY_MARGIN = 2000.0
    AUTOMATION_TAX_RATE = 0.05
    SEVERANCE_PAY_WEEKS = 4
    FIRM_MIN_PRODUCTION_TARGET = 10.0
    FIRM_MAX_PRODUCTION_TARGET = 500.0
    OVERSTOCK_THRESHOLD = 1.2
    UNDERSTOCK_THRESHOLD = 0.8
    PRODUCTION_ADJUSTMENT_FACTOR = 0.1
    SEO_TRIGGER_RATIO = 0.5
    SEO_MAX_SELL_RATIO = 0.1
    STARTUP_COST = 30000.0
    LABOR_ALPHA = 0.7
    AUTOMATION_LABOR_REDUCTION = 0.5
    INVISIBLE_HAND_SENSITIVITY = 0.1
    ALTMAN_Z_SCORE_THRESHOLD = 1.81
    DIVIDEND_SUSPENSION_LOSS_TICKS = 3

    # New fields
    INITIAL_FIRM_LIQUIDITY_NEED = 1000.0
    BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD = 5
    PROFIT_HISTORY_TICKS = 10
    IPO_INITIAL_SHARES = 1000
    INVENTORY_HOLDING_COST_RATE = 0.01
    FIRM_MAINTENANCE_FEE = 10.0
    CORPORATE_TAX_RATE = 0.2
    BAILOUT_REPAYMENT_RATIO = 0.1
    VALUATION_PER_MULTIPLIER = 10.0
    CAPITAL_DEPRECIATION_RATE = 0.01
    LABOR_ELASTICITY_MIN = 0.1
    HALO_EFFECT = 0.1
    MARKETING_DECAY_RATE = 0.1
    MARKETING_EFFICIENCY = 1.0
    PERCEIVED_QUALITY_ALPHA = 0.5
    BRAND_AWARENESS_SATURATION = 100.0
    MARKETING_EFFICIENCY_HIGH_THRESHOLD = 0.8
    MARKETING_EFFICIENCY_LOW_THRESHOLD = 0.2
    MARKETING_BUDGET_RATE_MIN = 0.01
    MARKETING_BUDGET_RATE_MAX = 0.1

@pytest.fixture
def firm_config_dto():
    c = MockConfig()
    # Use factory with overrides from MockConfig if needed, but factory defaults should suffice for general tests
    # We pass values from MockConfig to ensure tests that rely on specific values (like LABOR_ALPHA) still pass.
    return create_firm_config_dto(
        firm_min_production_target=c.FIRM_MIN_PRODUCTION_TARGET,
        firm_max_production_target=c.FIRM_MAX_PRODUCTION_TARGET,
        startup_cost=c.STARTUP_COST,
        seo_trigger_ratio=c.SEO_TRIGGER_RATIO,
        seo_max_sell_ratio=c.SEO_MAX_SELL_RATIO,
        automation_cost_per_pct=c.AUTOMATION_COST_PER_PCT,
        firm_safety_margin=c.FIRM_SAFETY_MARGIN,
        automation_tax_rate=c.AUTOMATION_TAX_RATE,
        altman_z_score_threshold=c.ALTMAN_Z_SCORE_THRESHOLD,
        dividend_suspension_loss_ticks=c.DIVIDEND_SUSPENSION_LOSS_TICKS,
        dividend_rate=c.DIVIDEND_RATE,
        dividend_rate_min=c.DIVIDEND_RATE_MIN,
        dividend_rate_max=c.DIVIDEND_RATE_MAX,
        labor_alpha=c.LABOR_ALPHA,
        automation_labor_reduction=c.AUTOMATION_LABOR_REDUCTION,
        severance_pay_weeks=float(c.SEVERANCE_PAY_WEEKS),
        labor_market_min_wage=c.LABOR_MARKET_MIN_WAGE,
        overstock_threshold=c.OVERSTOCK_THRESHOLD,
        understock_threshold=c.UNDERSTOCK_THRESHOLD,
        production_adjustment_factor=c.PRODUCTION_ADJUSTMENT_FACTOR,
        max_sell_quantity=float(c.MAX_SELL_QUANTITY),
        invisible_hand_sensitivity=c.INVISIBLE_HAND_SENSITIVITY,
        capital_to_output_ratio=c.CAPITAL_TO_OUTPUT_RATIO,
        initial_firm_liquidity_need=c.INITIAL_FIRM_LIQUIDITY_NEED,
        bankruptcy_consecutive_loss_threshold=c.BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD,
        profit_history_ticks=c.PROFIT_HISTORY_TICKS,
        ipo_initial_shares=float(c.IPO_INITIAL_SHARES),
        inventory_holding_cost_rate=c.INVENTORY_HOLDING_COST_RATE,
        firm_maintenance_fee=c.FIRM_MAINTENANCE_FEE,
        corporate_tax_rate=c.CORPORATE_TAX_RATE,
        bailout_repayment_ratio=c.BAILOUT_REPAYMENT_RATIO,
        valuation_per_multiplier=c.VALUATION_PER_MULTIPLIER,
        capital_depreciation_rate=c.CAPITAL_DEPRECIATION_RATE,
        labor_elasticity_min=c.LABOR_ELASTICITY_MIN,
        goods=c.GOODS,
        halo_effect=c.HALO_EFFECT,
        marketing_decay_rate=c.MARKETING_DECAY_RATE,
        marketing_efficiency=c.MARKETING_EFFICIENCY,
        perceived_quality_alpha=c.PERCEIVED_QUALITY_ALPHA,
        brand_awareness_saturation=c.BRAND_AWARENESS_SATURATION,
        marketing_efficiency_high_threshold=c.MARKETING_EFFICIENCY_HIGH_THRESHOLD,
        marketing_efficiency_low_threshold=c.MARKETING_EFFICIENCY_LOW_THRESHOLD,
        marketing_budget_rate_min=c.MARKETING_BUDGET_RATE_MIN,
        marketing_budget_rate_max=c.MARKETING_BUDGET_RATE_MAX,
        initial_base_annual_rate=0.05,
        default_loan_spread=0.02
    )

@pytest.fixture
def firm_dto():
    finance = FinanceStateDTO(
        balance=10000.0,
        revenue_this_turn=200.0,
        expenses_this_tick=100.0,
        consecutive_loss_turns=0,
        profit_history=[],
        altman_z_score=3.0,
        valuation=1000.0,
        total_shares=100.0,
        treasury_shares=0.0,
        dividend_rate=0.1,
        is_publicly_traded=True
    )

    production = ProductionStateDTO(
        current_production=0.0,
        productivity_factor=1.0,
        production_target=100.0,
        capital_stock=100.0,
        base_quality=1.0,
        automation_level=0.0,
        specialization="food",
        inventory={"food": 50.0},
        input_inventory={},
        inventory_quality={"food": 1.0}
    )

    sales = SalesStateDTO(
        inventory_last_sale_tick={},
        price_history={"food": 10.0},
        brand_awareness=0.0,
        perceived_quality=1.0,
        marketing_budget=0.0
    )

    hr = HRStateDTO(
        employees=[],
        employees_data={}
    )

    return FirmStateDTO(
        id=1,
        is_active=True,
        finance=finance,
        production=production,
        sales=sales,
        hr=hr,
        agent_data={"personality": "BALANCED"},
        system2_guidance={},
        sentiment_index=1.0
    )

@pytest.fixture
def context_mock(firm_dto, firm_config_dto):
    context = MagicMock(spec=DecisionContext)
    context.state = firm_dto # Use state
    context.config = firm_config_dto
    context.current_time = 1
    context.market_data = {
        "goods_market": {
            "food_avg_traded_price": 10.0,
            "food_current_sell_price": 10.0
        },
        "debt_data": {1: {"total_principal": 0.0}}
    }
    context.goods_data = [{"id": "food", "production_cost": 10.0, "inputs": {}}]
    context.reflux_system = MagicMock()
    return context
