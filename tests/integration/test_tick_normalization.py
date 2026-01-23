import pytest
from unittest.mock import MagicMock, Mock
from simulation.tick_scheduler import TickScheduler
from simulation.models import Transaction
from simulation.world_state import WorldState
from simulation.dtos.api import SimulationState

class TestTickNormalization:
    @pytest.fixture
    def mock_world_state(self):
        # Remove spec=WorldState to avoid AttributeError on missing attributes like social_system
        state = MagicMock()
        state.time = 0
        state.agents = {}
        state.firms = []
        state.households = []
        state.markets = {}
        state.transactions = []

        # Components
        state.bank = MagicMock()
        # Mock run_tick to return a test transaction
        state.bank.run_tick.return_value = [
            Transaction(0, 1, "test_item", 1.0, 10.0, "financial", "test_type", 0)
        ]

        state.finance_system = MagicMock()
        state.finance_system.service_debt.return_value = []

        state.government = MagicMock()
        state.government.run_welfare_check.return_value = []
        # Return (success, txs)
        state.government.invest_infrastructure.return_value = (True, [])
        # Fix: Mock get_monetary_delta to return float
        state.government.get_monetary_delta.return_value = 0.0

        state.tracker = MagicMock()
        state.tracker.get_latest_indicators.return_value = {}

        state.transaction_processor = MagicMock()

        # Mocks needed for sim_state construction
        state.config_module = MagicMock()
        state.config_module.INFRASTRUCTURE_TFP_BOOST = 0.05
        state.config_module.IMITATION_LEARNING_INTERVAL = 100 # Avoid modulo error if any

        state.logger = MagicMock()
        state.reflux_system = MagicMock()
        state.central_bank = MagicMock()
        state.stock_market = None
        state.goods_data = []
        state.next_agent_id = 100
        state.real_estate_units = []

        # Tech manager
        state.technology_manager = MagicMock()

        # Systems
        state.ma_manager = MagicMock()
        state.event_system = None
        state.commerce_system = None
        state.housing_system = MagicMock()
        state.crisis_monitor = None
        state.generational_wealth_audit = None

        # Fix format issue
        state.calculate_total_money = MagicMock(return_value=1000.0)
        state.baseline_money_supply = 1000.0

        return state

    @pytest.fixture
    def scheduler(self, mock_world_state):
        processor = MagicMock()
        return TickScheduler(mock_world_state, processor)

    def test_run_tick_collects_transactions(self, scheduler, mock_world_state):
        # Setup Firm
        mock_firm = MagicMock()
        mock_firm.id = 50
        mock_firm.is_active = True
        # Mock generate_transactions to return a tax transaction
        mock_firm.generate_transactions.return_value = [
            Transaction(50, 0, "corporate_tax", 1.0, 50.0, "system", "tax", 0)
        ]
        # Mock produce
        mock_firm.produce = MagicMock()
        mock_firm.update_needs = MagicMock()

        # Add firm to state
        mock_world_state.firms = [mock_firm]
        mock_world_state.agents = {50: mock_firm}

        # Prepare mock for _phase_decisions to avoid errors
        # (It returns tuple of dicts)
        scheduler._phase_decisions = MagicMock(return_value=({}, {}, {}))
        scheduler._phase_matching = MagicMock()
        scheduler._phase_lifecycle = MagicMock()
        scheduler.prepare_market_data = MagicMock(return_value={})

        # Act
        scheduler.run_tick()

        # Assertions

        # 1. Firm Produce called (Pre-Decision)
        mock_firm.produce.assert_called_once()

        # 2. Bank run_tick called
        mock_world_state.bank.run_tick.assert_called_once()

        # 3. Firm generate_transactions called
        mock_firm.generate_transactions.assert_called_once()

        # 4. Check TransactionProcessor call
        assert mock_world_state.transaction_processor.execute.called

        # Verify passed transactions
        args, _ = mock_world_state.transaction_processor.execute.call_args
        sim_state_dto = args[0]
        assert isinstance(sim_state_dto, SimulationState)

        transactions = sim_state_dto.transactions
        # Should contain Bank Tx (1) + Firm Tx (1) = 2
        assert len(transactions) >= 2

        tx_types = [tx.transaction_type for tx in transactions]
        assert "test_type" in tx_types
        assert "tax" in tx_types
