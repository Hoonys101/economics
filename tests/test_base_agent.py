import pytest
import os
import sys
from unittest.mock import Mock

from simulation.base_agent import BaseAgent
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.decisions.firm_decision_engine import FirmDecisionEngine

# 프로젝트 루트 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock Decision Engines for testing
class MockHouseholdDecisionEngine(HouseholdDecisionEngine):
    def __init__(self):
        pass
    def make_decisions(self, household, market_data, current_time):
        return []

class MockFirmDecisionEngine(FirmDecisionEngine):
    def __init__(self):
        pass
    def make_decisions(self, firm, market_data, current_time):
        return []

# Test BaseAgent abstract methods
def test_base_agent_abstract_methods():
    with pytest.raises(TypeError):
        BaseAgent(id=1, initial_assets=100.0, initial_needs={}, decision_engine=None)

    class ConcreteAgent(BaseAgent):
        def update_needs(self, current_tick: int):
            pass
        def make_decision(self, current_tick: int, market_data: dict):
            pass

    agent = ConcreteAgent(id=1, initial_assets=100.0, initial_needs={}, decision_engine=None, value_orientation=Mock(), logger=Mock())
    assert isinstance(agent, BaseAgent)

# ... (rest of the imports)

# Test Household inheritance and initialization
def test_household_inheritance_and_init():
    initial_assets = 100.0
    initial_needs = {"survival_need": 50.0, "wealth_need": 10.0, "labor_need": 0.0, "imitation_need": 0.0, "child_rearing_need": 0.0}
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
        logger=mock_logger
    )

    assert isinstance(household, BaseAgent)
    assert household.id == 1
    assert household.assets == initial_assets
    assert household.needs == initial_needs
    assert household.decision_engine == decision_engine
    assert household.name == "Household_1"
    assert household.talent == talent

# Test Firm inheritance and initialization
def test_firm_inheritance_and_init():
    initial_capital = 500.0
    initial_liquidity_need = 10.0 # Define this variable
    production_targets = {"food": 10}
    productivity_factor = 1.0
    decision_engine = MockFirmDecisionEngine()
    mock_logger = Mock()

    firm = Firm(
        id=101,
        initial_capital=initial_capital,
        initial_liquidity_need=10.0, # Add this back
        production_targets=production_targets,
        productivity_factor=productivity_factor,
        decision_engine=decision_engine,
        value_orientation=Mock(),
        logger=mock_logger
    )

    assert isinstance(firm, BaseAgent)
    assert firm.id == 101
    assert firm.assets == initial_capital
    assert firm.needs == {"liquidity_need": initial_liquidity_need}
    assert firm.decision_engine == decision_engine
    assert firm.name == "Firm_101"
    assert firm.production_targets == production_targets
    assert firm.productivity_factor == productivity_factor

