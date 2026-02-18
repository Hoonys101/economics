import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.death_system import DeathSystem
from simulation.dtos.api import SimulationState
from simulation.firms import Firm

class TestDeathSystem:
    @pytest.fixture
    def death_system(self):
        config = MagicMock()
        inheritance_manager = MagicMock()
        liquidation_manager = MagicMock()
        settlement_system = MagicMock()
        public_manager = MagicMock()
        logger = MagicMock()

        return DeathSystem(config, inheritance_manager, liquidation_manager, settlement_system, public_manager, logger)

    def test_firm_liquidation(self, death_system):
        firm = MagicMock(spec=Firm)
        firm.is_active = False
        firm.id = 1
        firm.get_all_items.return_value = {}

        firm.hr_state = MagicMock()
        firm.hr_state.employees = []

        firm.capital_stock = 100
        # Ensure ILiquidatable methods are present (Firm has them)

        state = MagicMock()
        state.firms = [firm]
        state.households = []
        state.agents = {1: firm}
        state.time = 1
        state.markets = {} # Ensure markets exists
        state.inactive_agents = None
        state.government = None # Prevent inheritance logic if any

        death_system.execute(state)

        death_system.liquidation_manager.initiate_liquidation.assert_called_once_with(firm, state)

        # Verify removal from global list
        assert firm not in state.firms
