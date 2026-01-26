
import pytest
from unittest.mock import MagicMock
from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household
from simulation.ai.api import Personality

@pytest.fixture
def demographic_manager_context():
    config_module = MagicMock()
    # Set defaults
    config_module.REPRODUCTION_AGE_START = 20
    config_module.REPRODUCTION_AGE_END = 50
    config_module.INITIAL_WAGE = 10.0
    config_module.EDUCATION_COST_MULTIPLIERS = {}
    config_module.NEWBORN_ENGINE_TYPE = "AIDriven"
    config_module.VALUE_ORIENTATION_MAPPING = {}
    config_module.SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 0.5
    config_module.FOOD_PURCHASE_MAX_PER_TICK = 5.0
    config_module.ASSETS_THRESHOLD_FOR_OTHER_ACTIONS = 100
    config_module.LABOR_MARKET_MIN_WAGE = 5.0
    config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD = 100
    config_module.HOUSEHOLD_LOW_ASSET_WAGE = 5.0
    config_module.HOUSEHOLD_DEFAULT_WAGE = 10.0
    config_module.MARKET_PRICE_FALLBACK = 1.0
    config_module.NEED_FACTOR_BASE = 1.0
    config_module.NEED_FACTOR_SCALE = 1.0
    config_module.VALUATION_MODIFIER_BASE = 1.0
    config_module.VALUATION_MODIFIER_RANGE = 0.1
    config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
    config_module.BULK_BUY_NEED_THRESHOLD = 0.8
    config_module.BULK_BUY_AGG_THRESHOLD = 0.8
    config_module.BULK_BUY_MODERATE_RATIO = 1.0
    config_module.DSR_CRITICAL_THRESHOLD = 0.5
    config_module.BUDGET_LIMIT_NORMAL_RATIO = 0.8
    config_module.BUDGET_LIMIT_URGENT_NEED = 1.0
    config_module.BUDGET_LIMIT_URGENT_RATIO = 1.0
    config_module.MIN_PURCHASE_QUANTITY = 1.0
    config_module.JOB_QUIT_THRESHOLD_BASE = 0.5
    config_module.JOB_QUIT_PROB_BASE = 0.1
    config_module.JOB_QUIT_PROB_SCALE = 0.1
    config_module.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 1000
    config_module.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 0.1
    config_module.STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 5
    config_module.DEBT_REPAYMENT_RATIO = 0.1
    config_module.DEBT_REPAYMENT_CAP = 100
    config_module.DEBT_LIQUIDITY_RATIO = 0.5
    config_module.INITIAL_RENT_PRICE = 100
    config_module.DEFAULT_MORTGAGE_RATE = 0.05
    config_module.MITOSIS_MUTATION_PROBABILITY = 0.1
    config_module.CONFORMITY_RANGES = {"low": (0, 0.3), "medium": (0.3, 0.7), "high": (0.7, 1.0)}
    config_module.INITIAL_HOUSEHOLD_ASSETS_MEAN = 1000
    config_module.QUALITY_PREF_MISER_MAX = 0.3
    config_module.QUALITY_PREF_SNOB_MIN = 0.7
    config_module.SOCIAL_STATUS_ASSET_WEIGHT = 0.5

    manager = DemographicManager(config_module=config_module)

    simulation = MagicMock()
    simulation.next_agent_id = 100
    simulation.goods_data = [{"id": "food", "price": 10}]
    simulation.markets = {"loan_market": MagicMock()}
    simulation.time = 1

    simulation.ai_trainer = MagicMock()
    simulation.ai_trainer.get_engine.return_value = MagicMock()

    return manager, simulation

def test_newborn_has_initial_needs(demographic_manager_context):
    manager, simulation = demographic_manager_context

    parent = MagicMock(spec=Household)
    parent.id = 1
    parent.age = 30
    parent.assets = 1000
    parent.talent = MagicMock()
    parent.personality = MagicMock()
    parent.personality.name = "Conscientious"
    parent.value_orientation = "wealth_and_needs"
    parent.risk_aversion = 0.5
    parent.generation = 1
    parent.children_ids = []
    parent._sub_assets = MagicMock()

    birth_requests = [parent]
    new_children = manager.process_births(simulation, birth_requests)

    assert len(new_children) == 1
    child = new_children[0]

    expected_needs = {
        "survival": 60.0,
        "social": 20.0,
        "improvement": 10.0,
        "asset": 10.0,
        "imitation_need": 15.0,
        "labor_need": 0.0,
        "liquidity_need": 50.0
    }

    assert child.needs == expected_needs
    assert "survival" in child.needs
