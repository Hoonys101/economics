import pytest
import os
import sys
from unittest.mock import Mock
from typing import Dict, Any

from simulation.base_agent import BaseAgent
from simulation.core_agents import Household, Talent, Personality
from simulation.firms import Firm
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config

# 프로젝트 루트 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Mock Decision Engines for testing
class MockHouseholdDecisionEngine(AIDrivenHouseholdDecisionEngine):
    def __init__(self):
        self.ai_engine = Mock()
        self.ai_engine.ai_decision_engine = Mock()
        self.ai_engine.gamma = 0.99
        self.ai_engine.action_selector.epsilon = 0.1
        self.ai_engine.base_alpha = 0.1
        self.ai_engine.learning_focus = 0.5
        self.config_module = config
        self.logger = Mock()

    def make_decisions(self, household, market_data, current_time):
        return [], None


class MockFirmDecisionEngine(AIDrivenFirmDecisionEngine):
    def __init__(self):
        pass

    def make_decisions(self, firm, market_data, current_time):
        return [], None


# Test BaseAgent abstract methods
def test_base_agent_abstract_methods():
    with pytest.raises(TypeError):
        BaseAgent(id=1, initial_assets=100.0, initial_needs={}, decision_engine=None)

    class ConcreteAgent(BaseAgent):
        def update_needs(self, current_tick: int):
            pass

        def make_decision(
            self,
            markets: Dict[str, Any],
            goods_data: list[Dict[str, Any]],
            market_data: Dict[str, Any],
            current_time: int,
        ) -> tuple[list[Any], Any]:
            return [], None

        def clone(
            self, new_id: int, initial_assets_from_parent: float, current_tick: int
        ) -> "BaseAgent":
            pass

    agent = ConcreteAgent(
        id=1,
        initial_assets=100.0,
        initial_needs={},
        decision_engine=None,
        value_orientation=Mock(),
        logger=Mock(),
    )
    assert isinstance(agent, BaseAgent)


# Test Household inheritance and initialization
def test_household_clone():
    initial_assets = 100.0
    initial_needs = {
        "survival_need": 50.0,
        "wealth_need": 10.0,
        "labor_need": 0.0,
        "imitation_need": 0.0,
        "child_rearing_need": 0.0,
    }
    talent = Talent(base_learning_rate=1.0, max_potential={})
    goods_data = []
    decision_engine = MockHouseholdDecisionEngine()
    mock_logger = Mock()

    household = Household(
        id=1,
        talent=talent,
        goods_data=goods_data,
        initial_assets=initial_assets,
        initial_needs=initial_needs,
        decision_engine=decision_engine,
        value_orientation=Mock(),
        logger=mock_logger,
        personality=Personality.MISER,
        config_module=config,
    )

    clone = household.clone(2, 50.0, 1)

    assert isinstance(clone, BaseAgent)
    assert clone.id == 2
    assert clone.assets == 50.0
    # assert household.needs == initial_needs
    assert clone.name == "Household_2"
    assert clone.talent == talent
    assert clone.demographics.parent_id == 1
    assert clone.demographics.generation == 1


# Test Firm inheritance and initialization
def test_firm_inheritance_and_init():
    initial_capital = 500.0
    initial_liquidity_need = 10.0  # Define this variable
    #     production_targets = {"food": 10}
    productivity_factor = 1.0
    decision_engine = MockFirmDecisionEngine()
    mock_logger = Mock()
    mock_config = Mock(spec=config)
    mock_config.PROFIT_HISTORY_TICKS = 10
    mock_config.FIRM_MIN_PRODUCTION_TARGET = 10.0

    firm = Firm(
        id=101,
        initial_capital=initial_capital,
        initial_liquidity_need=10.0,  # Add this back
        specialization="basic_food",  # Use specialization instead of production_targets
        productivity_factor=productivity_factor,
        decision_engine=decision_engine,
        value_orientation=Mock(),
        logger=mock_logger,
        config_module=mock_config,
    )

    assert isinstance(firm, BaseAgent)
    assert firm.id == 101
    assert firm.assets == initial_capital
    assert firm.needs == {"liquidity_need": initial_liquidity_need}
    assert firm.decision_engine == decision_engine
    assert firm.name == "Firm_101"
    assert firm.specialization == "basic_food"
    assert firm.production_target == 10.0
    assert firm.productivity_factor == productivity_factor
