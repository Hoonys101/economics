import pytest
from unittest.mock import Mock
from typing import Dict, Any, List

from simulation.base_agent import BaseAgent
from simulation.core_agents import Household, Talent, Personality
from simulation.firms import Firm
from modules.simulation.api import AgentCoreConfigDTO, AgentStateDTO, IDecisionEngine, IOrchestratorAgent
from simulation.dtos.config_dtos import HouseholdConfigDTO, FirmConfigDTO
import config
from simulation.utils.config_factory import create_config_dto
from modules.system.api import DEFAULT_CURRENCY

# Mock Decision Engine
class MockDecisionEngine:
    def __init__(self):
        self.loan_market = None
        self.logger = None
        self.ai_engine = Mock() # For clone mixin access
        self.ai_engine.ai_decision_engine = Mock()
        self.ai_engine.gamma = 0.99
        self.ai_engine.action_selector = Mock()
        self.ai_engine.action_selector.epsilon = 0.1
        self.ai_engine.base_alpha = 0.1
        self.ai_engine.learning_focus = 0.5

    def make_decision(self, state: AgentStateDTO, world_context: Any):
        return [], None
    def make_decisions(self, *args, **kwargs):
        return [], None

# Concrete BaseAgent implementation for testing
class ConcreteAgent(BaseAgent):
    def update_needs(self, current_tick: int):
        pass

    def make_decision(self, input_dto: Any) -> tuple[list[Any], Any]:
        return [], None

    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "BaseAgent":
        return ConcreteAgent(
            core_config=AgentCoreConfigDTO(
                id=new_id, name=f"ConcreteAgent_{new_id}",
                value_orientation=self.value_orientation,
                initial_needs=self.needs.copy(),
                logger=self.logger,
                memory_interface=self.memory_v2
            ),
            engine=self.decision_engine
        )

    def get_agent_data(self):
        return {}

def test_base_agent_initialization():
    core_config = AgentCoreConfigDTO(
        id=1,
        name="TestAgent",
        value_orientation="growth",
        initial_needs={"survival": 10.0},
        logger=Mock(),
        memory_interface=None
    )
    engine = MockDecisionEngine()

    agent = ConcreteAgent(core_config, engine)

    assert agent.id == 1
    assert agent.name == "TestAgent"
    assert agent.value_orientation == "growth"
    assert agent.needs == {"survival": 10.0}
    assert agent.wallet.get_balance(DEFAULT_CURRENCY) == 0.0 # Initially empty

    # Load State
    state = AgentStateDTO(
        assets={DEFAULT_CURRENCY: 100.0},
        inventory={"food": 5.0},
        is_active=True
    )
    agent.load_state(state)

    assert agent.wallet.get_balance(DEFAULT_CURRENCY) == 100.0
    assert agent.assets == 100.0
    assert agent.get_quantity("food") == 5.0
    assert agent.is_active is True

def test_household_initialization():
    core_config = AgentCoreConfigDTO(
        id=100,
        name="Household_100",
        value_orientation="needs",
        initial_needs={"survival": 5.0},
        logger=Mock(),
        memory_interface=None
    )
    engine = MockDecisionEngine()
    talent = Talent(1.0, {})
    hh_config = create_config_dto(config, HouseholdConfigDTO)

    household = Household(
        core_config=core_config,
        engine=engine,
        talent=talent,
        goods_data=[],
        personality=Personality.MISER,
        config_dto=hh_config
    )

    # Initially 0 assets
    assert household.assets == 0.0

    # Load State
    state = AgentStateDTO(
        assets={DEFAULT_CURRENCY: 500.0},
        inventory={},
        is_active=True
    )
    household.load_state(state)

    assert household.assets == 500.0
    assert household._econ_state.wallet.get_balance(DEFAULT_CURRENCY) == 500.0

def test_household_clone():
    core_config = AgentCoreConfigDTO(
        id=100,
        name="Household_100",
        value_orientation="needs",
        initial_needs={"survival": 5.0},
        logger=Mock(),
        memory_interface=None
    )
    engine = MockDecisionEngine()
    talent = Talent(1.0, {})
    hh_config = create_config_dto(config, HouseholdConfigDTO)

    household = Household(
        core_config=core_config,
        engine=engine,
        talent=talent,
        goods_data=[],
        personality=Personality.MISER,
        config_dto=hh_config
    )
    # Give some assets
    household.load_state(AgentStateDTO(assets={DEFAULT_CURRENCY: 100.0}, inventory={}, is_active=True))

    # Clone
    child = household.clone(101, 50.0, 1)

    assert child.id == 101
    assert child.assets == 50.0
    assert child.name == "Household_101"

def test_firm_initialization():
    core_config = AgentCoreConfigDTO(
        id=200,
        name="Firm_200",
        value_orientation="profit",
        initial_needs={"liquidity_need": 100.0},
        logger=Mock(),
        memory_interface=None
    )
    engine = MockDecisionEngine()
    firm_config = create_config_dto(config, FirmConfigDTO)

    firm = Firm(
        core_config=core_config,
        engine=engine,
        specialization="food",
        productivity_factor=1.2,
        config_dto=firm_config
    )

    assert firm.assets == 0.0
    assert firm.specialization == "food"

    # Load State
    state = AgentStateDTO(
        assets={DEFAULT_CURRENCY: 1000.0},
        inventory={"raw_material": 50.0},
        is_active=True
    )
    firm.load_state(state)

    assert firm.assets == 1000.0
    assert firm.get_quantity("raw_material") == 50.0
