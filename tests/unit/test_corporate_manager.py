
import pytest
from unittest.mock import MagicMock
from simulation.decisions.corporate_manager import CorporateManager
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.schemas import FirmActionVector
from simulation.models import Order
from simulation.ai.enums import Personality

class MockConfig:
    CAPITAL_TO_OUTPUT_RATIO = 2.0
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

@pytest.fixture
def firm_config_dto():
    c = MockConfig()
    return FirmConfigDTO(
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
        capital_to_output_ratio=c.CAPITAL_TO_OUTPUT_RATIO
    )

@pytest.fixture
def firm_dto():
    return FirmStateDTO(
        id=1,
        assets=10000.0,
        is_active=True,
        inventory={"food": 50.0},
        inventory_quality={"food": 1.0},
        input_inventory={},
        current_production=0.0,
        productivity_factor=1.0,
        production_target=100.0,
        capital_stock=100.0,
        base_quality=1.0,
        automation_level=0.0,
        specialization="food",
        total_shares=100.0,
        treasury_shares=0.0,
        dividend_rate=0.1,
        is_publicly_traded=True,
        valuation=1000.0,
        revenue_this_turn=200.0,
        expenses_this_tick=100.0,
        consecutive_loss_turns=0,
        altman_z_score=3.0,
        price_history={"food": 10.0},
        profit_history=[],
        brand_awareness=0.0,
        perceived_quality=1.0,
        marketing_budget=0.0,
        employees=[],
        employees_data={},
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

def test_rd_logic(firm_dto, context_mock):
    manager = CorporateManager(MockConfig())
    # Aggressiveness 1.0 -> 20% of Revenue
    vector = FirmActionVector(
        rd_aggressiveness=1.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0,
        hiring_aggressiveness=0.0,
        sales_aggressiveness=0.0
    )

    firm_dto.assets = 10000.0
    firm_dto.revenue_this_turn = 1000.0
    expected_budget = 1000.0 * 0.2 # 200

    orders = manager.realize_ceo_actions(firm_dto, context_mock, vector)

    rd_orders = [o for o in orders if o.order_type == "INVEST_RD"]
    assert len(rd_orders) == 1
    assert rd_orders[0].quantity == expected_budget
    assert rd_orders[0].market_id == "internal"

def test_dividend_logic(firm_dto, context_mock):
    manager = CorporateManager(MockConfig())
    vector = FirmActionVector(dividend_aggressiveness=1.0) # Max rate 0.5

    orders = manager.realize_ceo_actions(firm_dto, context_mock, vector)

    div_orders = [o for o in orders if o.order_type == "SET_DIVIDEND"]
    assert len(div_orders) == 1
    assert div_orders[0].quantity == 0.5

def test_hiring_logic(firm_dto, context_mock):
    manager = CorporateManager(MockConfig())
    firm_dto.production_target = 100
    firm_dto.inventory["food"] = 80 # Gap 20
    firm_dto.productivity_factor = 10.0 # Need 2 workers (approx)

    # Adjust mock to return empty list of employees so we hire
    firm_dto.employees = []

    vector = FirmActionVector(hiring_aggressiveness=0.5)

    orders = manager.realize_ceo_actions(firm_dto, context_mock, vector)

    hiring_orders = [o for o in orders if o.order_type == "BUY" and o.item_id == "labor"]
    assert len(hiring_orders) > 0
    assert hiring_orders[0].price >= 10.0

def test_debt_logic_borrow(firm_dto, context_mock):
    manager = CorporateManager(MockConfig())
    firm_dto.assets = 1000.0

    # Mock debt data
    context_mock.market_data["debt_data"] = {firm_dto.id: {"total_principal": 0.0}}

    vector = FirmActionVector(debt_aggressiveness=0.5)

    orders = manager.realize_ceo_actions(firm_dto, context_mock, vector)

    loan_reqs = [o for o in orders if o.order_type == "LOAN_REQUEST"]
    assert len(loan_reqs) > 0
    assert loan_reqs[0].quantity > 0

def test_automation_investment(firm_dto, context_mock):
    config = MockConfig()
    config.AUTOMATION_COST_PER_PCT = 10.0 # Make it cheap
    # Update config DTO
    context_mock.config.automation_cost_per_pct = 10.0

    manager = CorporateManager(config)
    # Ensure automation is profitable so System 2 recommends it
    # High wages so automation saves money
    firm_dto.employees_data = {
        1: {"wage": 2000.0, "skill": 1.0, "id": 1, "age": 20, "education_level": 1}
    }
    firm_dto.revenue_this_turn = 5000.0

    firm_dto.assets = 50000.0 # Plenty of cash

    vector = FirmActionVector(capital_aggressiveness=1.0)

    orders = manager.realize_ceo_actions(firm_dto, context_mock, vector)

    auto_orders = [o for o in orders if o.order_type == "INVEST_AUTOMATION"]
    assert len(auto_orders) > 0
    assert auto_orders[0].quantity > 0
