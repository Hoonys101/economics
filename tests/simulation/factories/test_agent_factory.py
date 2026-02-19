import pytest
from unittest.mock import MagicMock
from simulation.factories.household_factory import HouseholdFactory
from modules.household.api import HouseholdFactoryContext
from simulation.core_agents import Household
from simulation.models import Talent
from simulation.ai.api import Personality
from modules.simulation.dtos.api import HouseholdConfigDTO

@pytest.fixture
def mock_context(mock_config_module):
    context = HouseholdFactoryContext(
        core_config_module=mock_config_module,
        household_config_dto=MagicMock(),
        goods_data=[],
        loan_market=MagicMock(),
        ai_training_manager=MagicMock(),
        settlement_system=MagicMock(),
        markets=MagicMock(),
        memory_system=MagicMock(),
        central_bank=MagicMock(),
        demographic_manager=MagicMock()
    )
    return context

def test_create_household(mock_context):
    factory = HouseholdFactory(mock_context)
    
    mock_engine = MagicMock()
    mock_engine.value_orientation = "Growth"

    agent = factory.create_household(
        agent_id=1,
        initial_age=25.0,
        gender="M",
        initial_assets=100,
        decision_engine=mock_engine
    )

    assert isinstance(agent, Household)
    assert agent.id == 1
    assert agent.age == 25.0
    assert agent.gender == "M"
    assert agent.assets == 100.0

def test_create_newborn(mock_context):
    factory = HouseholdFactory(mock_context)
    
    parent = MagicMock(spec=Household)
    parent.id = 1
    parent.generation = 1
    parent.talent = Talent(base_learning_rate=1.0, max_potential={})
    parent.personality = Personality.Growth
    parent.value_orientation = "Growth"

    child = factory.create_newborn(
        parent=parent,
        new_id=2,
        initial_assets=0,
        current_tick=1
    )

    assert isinstance(child, Household)
    assert child.id == 2
    assert child.age == 0.0
    assert child.generation == 2
    assert child.parent_id == 1
