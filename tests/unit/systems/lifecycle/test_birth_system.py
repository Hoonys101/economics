import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.birth_system import BirthSystem
from simulation.dtos.api import SimulationState
from simulation.core_agents import Household
from modules.system.api import ICurrencyHolder

class TestBirthSystem:
    @pytest.fixture
    def birth_system(self):
        config = MagicMock()
        config.REPRODUCTION_AGE_START = 20
        config.REPRODUCTION_AGE_END = 40
        demographic_manager = MagicMock()
        immigration_manager = MagicMock()
        firm_system = MagicMock()
        settlement_system = MagicMock()
        logger = MagicMock()
        household_factory = MagicMock()

        system = BirthSystem(config, demographic_manager, immigration_manager, firm_system, settlement_system, logger, household_factory)
        system.breeding_planner = MagicMock()
        return system

    def test_process_births_with_factory(self, birth_system):
        # Avoid strict spec to allow _bio_state
        parent = MagicMock()
        parent._bio_state.is_active = True
        parent.age = 25
        parent.wallet.get_balance.return_value = 1000
        parent.children_ids = []
        # Mock class for isinstance check if needed, though MagicMock might handle it if not strict
        # But we can just rely on the fact that ICurrencyHolder is checked.
        # MagicMock usually returns True for isinstance checks if not specified?
        # No, isinstance(Mock(), Protocol) might be tricky.
        # Let's ensure parent and child pass the check.
        # We can spec them as ICurrencyHolder.

        # Actually, let's just make sure they look like ICurrencyHolder
        parent.balance_pennies = 0

        state = MagicMock()
        state.households = [parent]
        state.agents = {parent.id: parent}
        state.next_agent_id = 100
        state.time = 1
        state.markets = {}
        state.goods_data = {}
        state.stock_market = None
        state.ai_training_manager = None

        birth_system.breeding_planner.decide_breeding_batch.return_value = [True]

        child = MagicMock()
        child.id = 100

        birth_system.household_factory.create_newborn.return_value = child

        birth_system.execute(state)

        birth_system.household_factory.create_newborn.assert_called_once()
        assert child in state.households
