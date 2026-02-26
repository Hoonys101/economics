import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.death_system import DeathSystem
from simulation.systems.lifecycle.api import DeathConfigDTO
from simulation.dtos.api import SimulationState
from simulation.firms import Firm
from simulation.interfaces.market_interface import IMarket

class TestDeathSystem:
    @pytest.fixture
    def death_system(self):
        config = MagicMock(spec=DeathConfigDTO)
        config.default_fallback_price_pennies = 1000

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

    def test_firm_liquidation_cancels_orders(self, death_system):
        firm = MagicMock(spec=Firm)
        firm.is_active = False
        firm.id = 1
        firm.get_all_items.return_value = {}
        firm.hr_state = MagicMock()
        firm.hr_state.employees = []
        firm.liquidate_assets.return_value = {}

        # Setup Market
        # Use spec=IMarket so isinstance(mock_market, IMarket) returns True
        mock_market = MagicMock(spec=IMarket)
        # Ensure methods exist on the mock
        mock_market.cancel_orders = MagicMock()
        mock_market.id = "test_market"
        mock_market.buy_orders = {}
        mock_market.sell_orders = {}
        mock_market.matched_transactions = []

        state = MagicMock()
        state.firms = [firm]
        state.households = []
        state.agents = {1: firm}
        state.time = 1
        state.markets = {"test_market": mock_market}
        state.inactive_agents = {}
        state.government = None

        death_system.execute(state)

        mock_market.cancel_orders.assert_called_with(firm.id)
