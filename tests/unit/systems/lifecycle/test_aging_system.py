import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.aging_system import AgingSystem
from simulation.dtos.api import SimulationState

class TestAgingSystem:
    @pytest.fixture
    def aging_system(self):
        config = MagicMock()
        config.ASSETS_CLOSURE_THRESHOLD = 0.0
        config.FIRM_CLOSURE_TURNS_THRESHOLD = 5
        config.LIQUIDITY_NEED_INCREASE_RATE = 1.0
        config.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
        config.DISTRESS_GRACE_PERIOD = 5 # Mock the config value

        demographic_manager = MagicMock()
        logger = MagicMock()
        return AgingSystem(config, demographic_manager, logger)

    def test_execute_delegation(self, aging_system):
        # Use simple Mock to avoid attribute errors with dataclasses specs
        state = MagicMock()
        state.households = []
        state.firms = []
        state.time = 1
        state.market_data = {}

        aging_system.execute(state)

        aging_system.demographic_manager.process_aging.assert_called_once_with([], 1, {})

    def test_firm_distress(self, aging_system):
        firm = MagicMock()
        firm.is_active = True
        firm.age = 1
        firm.needs = {"liquidity_need": 0.0}
        firm.finance_state.distress_tick_counter = 0
        firm.finance_state.consecutive_loss_turns = 0
        firm.wallet.get_balance.return_value = -10.0 # Crunch
        firm.get_all_items.return_value = {"wood": 10.0}

        state = MagicMock()
        state.firms = [firm]
        # Ensure households is present to avoid AttributeError in execute
        state.households = []
        state.markets = {"wood": MagicMock(avg_price=10.0)}
        state.time = 1
        state.market_data = {}

        aging_system.execute(state)

        assert firm.finance_state.is_distressed is True
        assert firm.finance_state.distress_tick_counter == 1

    def test_firm_grace_period_config(self, aging_system):
        # Change grace period to 10
        aging_system.config.DISTRESS_GRACE_PERIOD = 10

        firm = MagicMock()
        firm.is_active = True
        firm.wallet.get_balance.return_value = -10.0
        firm.needs = {"liquidity_need": 0.0}
        firm.finance_state.distress_tick_counter = 9
        firm.get_all_items.return_value = {"wood": 10.0}

        state = MagicMock()
        state.firms = [firm]
        state.households = []
        state.markets = {"wood": MagicMock(avg_price=10.0)}
        state.time = 1
        state.market_data = {}

        aging_system.execute(state)

        # Should still be active (tick 10 <= 10)
        # Note: logic increments tick counter first. 9 -> 10.
        # if 10 <= 10: continue. So active=True.
        assert firm.finance_state.distress_tick_counter == 10
        assert firm.is_active is True
