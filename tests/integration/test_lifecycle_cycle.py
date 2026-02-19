import pytest
from unittest.mock import MagicMock, patch, ANY
from collections import deque
from simulation.orchestration.tick_orchestrator import TickOrchestrator
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from modules.system.api import DEFAULT_CURRENCY
from simulation.world_state import WorldState

class TestLifecycleCycle:
    @pytest.fixture
    def mock_world_state(self):
        state = MagicMock(spec=WorldState)
        state.time = 0
        state.agents = {}
        state.firms = []
        state.households = []
        state.markets = {}
        # Important: use real lists for queues to track movement
        state.transactions = []
        state.inter_tick_queue = []
        state.system_command_queue = []
        state.god_command_queue = deque()
        state.command_queue = MagicMock()
        state.command_queue.empty.return_value = True

        # Mocks
        state.bank = MagicMock()
        state.bank.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 0.0}

        state.lifecycle_manager = MagicMock()
        state.transaction_processor = MagicMock()

        state.config_module = MagicMock()
        state.logger = MagicMock()
        state.tracker = MagicMock()
        state.tracker.get_latest_indicators.return_value = {}

        state.calculate_total_money.return_value = {DEFAULT_CURRENCY: 1000}
        state.baseline_money_supply = 1000.0

        state.inactive_agents = {}
        state.effects_queue = []

        # Missing attributes
        state.stock_market = None
        state.stock_tracker = None
        state.goods_data = {}
        state.ai_training_manager = None
        state.ai_trainer = None
        state.settlement_system = MagicMock()
        state.taxation_system = MagicMock()
        state.currency_holders = []
        state.next_agent_id = 1
        state.real_estate_units = []
        state.stress_scenario_config = None
        state.saga_orchestrator = MagicMock()
        state.monetary_ledger = MagicMock()
        state.shareholder_registry = MagicMock()
        state.global_registry = MagicMock()
        state.inequality_tracker = MagicMock()

        state.technology_manager = MagicMock()
        state.ma_manager = None
        state.commerce_system = None
        state.housing_system = MagicMock()
        state.crisis_monitor = None
        state.generational_wealth_audit = None
        state.demographic_manager = None
        state.immigration_manager = None
        state.inheritance_manager = None
        state.persistence_manager = None
        state.analytics_system = None
        state.firm_system = None
        state.breeding_planner = None
        state.finance_system = None
        state.social_system = None
        state.event_system = None
        state.sensory_system = None
        state.labor_market_analyzer = None
        state.public_manager = None
        state.dashboard_service = None
        state.telemetry_exchange = None
        state.judicial_system = None
        state.escrow_agent = None
        state.scenario_verifier = None

        state.last_interest_rate = 0.05
        state.inflation_buffer = deque()
        state.unemployment_buffer = deque()
        state.gdp_growth_buffer = deque()
        state.wage_buffer = deque()
        state.approval_buffer = deque()
        state.last_avg_price_for_sma = 10.0
        state.last_gdp_for_sma = 0.0

        return state

    @pytest.fixture
    def orchestrator(self, mock_world_state):
        processor = MagicMock()
        return TickOrchestrator(mock_world_state, processor)

    def test_lifecycle_transactions_processed_in_next_tick_strong_verify(self, orchestrator, mock_world_state):
        # Capture processed transactions
        processed_txs = []
        def capture_txs(state, transactions):
            # Iterate through the chain/iterable and capture items
            tx_list = list(transactions)
            processed_txs.extend(tx_list)
            return []

        mock_world_state.transaction_processor.execute.side_effect = capture_txs

        # Setup
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="test", price=10.0, quantity=1,
            market_id="test_market", transaction_type="test", time=0,
            total_pennies=1000
        )
        mock_world_state.lifecycle_manager.execute.return_value = [tx]

        # Mock dependencies
        mock_world_state.social_system = MagicMock()
        mock_world_state.sensory_system = MagicMock()
        mock_world_state.government = MagicMock()
        mock_world_state.government.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 0.0}
        mock_world_state.government.get_monetary_delta.return_value = 0
        mock_world_state.central_bank = MagicMock()
        mock_world_state.central_bank.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 0.0}
        mock_world_state.event_system = None
        mock_world_state.persistence_manager = None

        # === TICK 1 ===
        orchestrator.run_tick()

        # Verify NOT processed in Tick 1
        assert tx not in processed_txs, "Transaction should NOT be processed in the same tick (Sacred Sequence)"
        processed_txs.clear()

        # Verify present in queue
        assert tx in mock_world_state.inter_tick_queue, "Transaction should be in inter_tick_queue"

        # Reset lifecycle manager return to ensure no new txs are generated in Tick 2
        mock_world_state.lifecycle_manager.execute.return_value = []

        # === TICK 2 ===
        orchestrator.run_tick()

        # Verify PROCESSED in Tick 2
        assert tx in processed_txs, "Transaction from previous tick should be processed in current tick"
        assert len(mock_world_state.inter_tick_queue) == 0, "Queue should be cleared"
