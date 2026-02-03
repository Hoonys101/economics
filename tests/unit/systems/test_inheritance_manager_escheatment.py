import pytest
from unittest.mock import MagicMock, ANY
from types import SimpleNamespace
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.models import Transaction

class TestInheritanceManagerEscheatment:

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        # Ensure config attributes used in InheritanceManager return float values, not Mocks
        config.INHERITANCE_TAX_RATE = 0.4
        config.INHERITANCE_DEDUCTION = 10000.0
        return config

    @pytest.fixture
    def inheritance_manager(self, mock_config):
        return InheritanceManager(mock_config)

    @pytest.fixture
    def mock_simulation(self):
        sim = MagicMock()
        sim.time = 100
        sim.real_estate_units = []
        sim.stock_market = MagicMock()
        sim.agents = MagicMock()
        return sim

    @pytest.fixture
    def mock_government(self):
        gov = MagicMock()
        gov.id = 1
        gov.agent_type = "government"
        return gov

    @pytest.fixture
    def mock_deceased(self):
        deceased = MagicMock()
        deceased.id = 101
        deceased._econ_state.assets = 0.0 # ZERO CASH
        deceased._bio_state.children_ids = [] # NO HEIRS

        # Portfolio setup (though create_settlement consumes it,
        # InheritanceManager reads it before calling create_settlement for valuation)
        deceased._econ_state.portfolio.holdings = {
            999: SimpleNamespace(quantity=10, acquisition_price=5.0)
        }
        return deceased

    def test_escheatment_portfolio_trigger_zero_cash(
        self, inheritance_manager, mock_simulation, mock_government, mock_deceased
    ):
        """
        TD-160: Verify that when cash is 0, Government is still added to distribution plan
        to ensure SettlementSystem triggers portfolio escheatment.
        """
        # Setup SettlementSystem Mock
        mock_settlement = MagicMock()
        mock_simulation.settlement_system = mock_settlement

        # Mock create_settlement return value (Account)
        mock_account = MagicMock()
        mock_account.deceased_agent_id = mock_deceased.id
        mock_account.escrow_cash = 0.0
        mock_account.escrow_portfolio.assets = ["some_asset"] # Simulate portfolio exists in escrow
        mock_account.is_escheatment = True

        mock_settlement.create_settlement.return_value = mock_account
        mock_settlement.execute_settlement.return_value = [] # Return empty receipts

        # Mock Stock Market for Valuation
        mock_simulation.stock_market.get_daily_avg_price.return_value = 10.0

        # Execute
        inheritance_manager.process_death(mock_deceased, mock_government, mock_simulation)

        # Verification
        # 1. create_settlement called
        mock_settlement.create_settlement.assert_called_once_with(agent=mock_deceased, tick=mock_simulation.time)

        # 2. execute_settlement called with Government in distribution plan
        # execute_settlement(account_id, distribution_plan, tick)
        call_args = mock_settlement.execute_settlement.call_args
        assert call_args is not None

        distribution_plan = call_args[0][1]

        # Check if Government is in the plan
        # Expected: [(government, 0.0, "escheatment_portfolio", "escheatment")] OR similar
        gov_in_plan = False
        for recipient, amount, memo, tx_type in distribution_plan:
            if recipient == mock_government:
                gov_in_plan = True
                # Optional: Check memo/type
                break

        assert gov_in_plan, "Government must be in distribution plan to trigger portfolio escheatment, even if cash is 0."
