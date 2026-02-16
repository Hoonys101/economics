import pytest
from unittest.mock import MagicMock
from simulation.factories.agent_factory import HouseholdFactory
from simulation.core_agents import Household
from simulation.models import Talent
from simulation.ai.enums import Personality
from modules.simulation.dtos.api import HouseholdConfigDTO

@pytest.fixture
def mock_config_module():
    config = MagicMock()
    config.INITIAL_HOUSEHOLD_AGE_RANGE = (20, 40)
    config.INITIAL_NEEDS = {"survival": 0.0}
    config.TICKS_PER_YEAR = 100
    config.PRICE_MEMORY_LENGTH = 10
    config.WAGE_MEMORY_LENGTH = 10
    config.INITIAL_APTITUDE_DISTRIBUTION = (0.5, 0.1)
    config.CONFORMITY_RANGES = {}
    config.VALUE_ORIENTATION_MAPPING = {}
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 100.0
    config.NEWBORN_INITIAL_NEEDS = {"survival": 0.0}
    config.MITOSIS_MUTATION_PROBABILITY = 0.0
    config.INITIAL_WAGE = 10.0
    config.DEFAULT_VALUE_ORIENTATION = "Growth"
    return config

def test_create_household(mock_config_module):
    factory = HouseholdFactory(mock_config_module)
    simulation = MagicMock()
    simulation.goods_data = []
    simulation.logger = MagicMock()

    mock_engine = MagicMock()
    mock_engine.value_orientation = "Growth"

    agent = factory.create_household(
        agent_id=1,
        simulation=simulation,
        initial_age=25.0,
        gender="M",
        initial_assets=100.0,
        decision_engine=mock_engine
    )

    assert isinstance(agent, Household)
    assert agent.id == 1
    assert agent.age == 25.0
    assert agent.gender == "M"
    assert agent.assets == 100.0

def test_create_newborn(mock_config_module):
    factory = HouseholdFactory(mock_config_module)
    simulation = MagicMock()
    simulation.goods_data = []
    simulation.logger = MagicMock()
    simulation.ai_trainer.get_engine.return_value = None
    simulation.markets.get.return_value = None

    parent = MagicMock(spec=Household)
    parent.id = 1
    parent.generation = 1
    parent.talent = Talent(base_learning_rate=1.0, max_potential={})
    parent.personality = Personality.CONSERVATIVE
    parent.value_orientation = "Growth"

    child = factory.create_newborn(
        parent=parent,
        simulation=simulation,
        new_id=2
    )

    assert isinstance(child, Household)
    assert child.id == 2
    assert child.age == 0.0
    assert child.generation == 2
    assert child.parent_id == 1
