import pytest
from unittest.mock import Mock, MagicMock
from simulation.decisions.household.consumption_manager import ConsumptionManager
from simulation.models import Order
from simulation.schemas import HouseholdActionVector
from tests.unit.factories import create_household_dto
from tests.utils.factories import create_household_config_dto
from simulation.ai.api import Personality

@pytest.fixture
def manager():
    return ConsumptionManager()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def base_household():
    return create_household_dto(
        id=1,
        assets=100.0,
        needs={"survival": 0.5},
        is_employed=False,
        current_wage=0.0,
        wage_modifier=1.0,
        personality=Personality.BALANCED
    )

@pytest.fixture
def base_config():
    config = Mock()
    config.survival_need_emergency_threshold = 0.8
    config.primary_survival_good_id = "basic_food"
    config.survival_bid_premium = 0.1
    return config

class TestConsumptionManagerSurvival:
    def test_check_survival_override_no_emergency(self, manager, base_household, base_config, mock_logger):
        # Survival need 0.5 < threshold 0.8
        base_household.needs["survival"] = 0.5
        market_snapshot = {}

        result = manager.check_survival_override(base_household, base_config, market_snapshot, 1, mock_logger)

        assert result is None

    def test_check_survival_override_emergency_triggered(self, manager, base_household, base_config, mock_logger):
        # Survival need 0.9 > threshold 0.8
        base_household.needs["survival"] = 0.9

        # Market signal
        market_snapshot = {
            "market_signals": {
                "basic_food": {"best_ask": 10.0}
            }
        }

        # Assets sufficient (100.0 > 10.0 * 1.1)
        base_household.assets = 100.0

        result = manager.check_survival_override(base_household, base_config, market_snapshot, 1, mock_logger)

        assert result is not None
        orders, vector = result

        assert isinstance(orders, list)
        assert len(orders) == 1
        assert orders[0].item_id == "basic_food"
        assert orders[0].side == "BUY"
        # Price = 10.0 * 1.1 = 11.0
        assert abs(orders[0].price_limit - 11.0) < 0.0001

        assert isinstance(vector, HouseholdActionVector)
        assert vector.work_aggressiveness == 1.0

    def test_check_survival_override_emergency_triggered_insufficient_funds(self, manager, base_household, base_config, mock_logger):
        base_household.needs["survival"] = 0.9

        market_snapshot = {
            "market_signals": {
                "basic_food": {"best_ask": 200.0} # Too expensive
            }
        }
        base_household.assets = 100.0

        result = manager.check_survival_override(base_household, base_config, market_snapshot, 1, mock_logger)

        assert result is None

    def test_check_survival_override_no_signal(self, manager, base_household, base_config, mock_logger):
        base_household.needs["survival"] = 0.9

        market_snapshot = {
            "market_signals": {} # No basic_food
        }

        result = manager.check_survival_override(base_household, base_config, market_snapshot, 1, mock_logger)

        assert result is None
