import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.birth_system import BirthSystem
from simulation.dtos.api import SimulationState
from simulation.core_agents import Household
from modules.system.api import ICurrencyHolder, DEFAULT_CURRENCY

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

        immigration_manager.process_immigration.return_value = []

        system = BirthSystem(config, demographic_manager, immigration_manager, firm_system, settlement_system, logger, household_factory)
        system.breeding_planner = MagicMock()
        return system

    def test_process_births_with_factory_zero_sum(self, birth_system):
        # Setup Parent with assets
        # Use spec=Household to satisfy isinstance(parent, ICurrencyHolder)
        parent = MagicMock(spec=Household)
        parent.id = 1
        parent.age = 25
        parent.is_active = True
        parent.children_ids = []
        # Mock methods required by ICurrencyHolder
        parent.get_balance.return_value = 1000
        parent.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 1000}

        # Setup State
        state = MagicMock()
        state.households = [parent]
        state.agents = {parent.id: parent}
        state.next_agent_id = 100
        state.time = 1
        state.markets = {}
        state.goods_data = {}
        state.stock_market = None
        state.ai_training_manager = None
        state.shareholder_registry = None

        # Mock Planner
        birth_system.breeding_planner.decide_breeding_batch.return_value = [True]

        # Mock Child
        child = MagicMock(spec=Household)
        child.id = 100
        child.portfolio.holdings.items.return_value = []
        child.decision_engine = MagicMock() # Explicitly mock decision_engine

        # Mock Factory to verify it receives 0 initial assets
        birth_system.household_factory.create_newborn.return_value = child

        # Execute
        transactions = birth_system.execute(state)

        # Assert Factory called with 0 assets
        birth_system.household_factory.create_newborn.assert_called_once()
        call_kwargs = birth_system.household_factory.create_newborn.call_args[1]
        assert call_kwargs.get('initial_assets') == 0

        # Assert SettlementSystem.transfer NOT called (Deferred Execution)
        birth_system.settlement_system.transfer.assert_not_called()

        # Assert Transaction Returned
        expected_gift = 100
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.item_id == "BIRTH_GIFT"
        assert tx.total_pennies == expected_gift
        assert tx.buyer_id == parent.id
        assert tx.seller_id == child.id
        assert tx.transaction_type == "GIFT"

        assert child in state.households
