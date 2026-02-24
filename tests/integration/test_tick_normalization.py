import pytest
from unittest.mock import MagicMock, Mock, patch
from collections import deque
from simulation.orchestration.tick_orchestrator import TickOrchestrator
from simulation.models import Transaction
from simulation.world_state import WorldState
from simulation.dtos.api import SimulationState
from modules.system.api import DEFAULT_CURRENCY

class TestTickNormalization:
    @pytest.fixture
    def mock_world_state(self):
        from simulation.world_state import WorldState
        # Use spec=WorldState to prevent Mock Drift
        state = MagicMock(spec=WorldState)
        state.time = 0
        state.agents = {}
        state.firms = []
        state.households = []
        state.markets = {}
        state.transactions = []
        state.inter_tick_queue = []
        state.effects_queue = []
        state.stock_tracker = None
        state.inactive_agents = {}
        state.global_registry = MagicMock()
        state.lifecycle_manager = MagicMock()

        # Components
        state.bank = MagicMock()
        state.bank.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 0.0}
        # Mock run_tick to return a test transaction
        state.bank.run_tick.return_value = [
            Transaction(0, 1, "test_item", 1.0, 10.0, "financial", "test_type", 0, total_pennies=1000)
        ]

        state.finance_system = MagicMock()
        state.finance_system.service_debt.return_value = []

        state.primary_government = MagicMock()
        state.government = state.primary_government # For legacy compatibility during refactor
        state.primary_government.run_welfare_check.return_value = []
        # Return (success, txs)
        state.primary_government.invest_infrastructure.return_value = []
        # Fix: Mock get_monetary_delta to return float
        state.primary_government.get_monetary_delta.return_value = 0.0
        state.primary_government.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 0.0}

        state.tracker = MagicMock()
        state.tracker.get_latest_indicators.return_value = {}

        state.transaction_processor = MagicMock()

        # Mocks needed for sim_state construction
        state.config_module = MagicMock()
        state.config_manager = MagicMock()
        state.config_module.INFRASTRUCTURE_TFP_BOOST = 0.05
        state.config_module.IMITATION_LEARNING_INTERVAL = 100 # Avoid modulo error if any

        state.logger = MagicMock()
        state.reflux_system = MagicMock()
        state.central_bank = MagicMock()
        state.central_bank.get_assets_by_currency.return_value = {DEFAULT_CURRENCY: 0.0}
        state.stock_market = None
        state.goods_data = []
        state.next_agent_id = 100
        state.real_estate_units = []

        # Tech manager
        state.technology_manager = MagicMock()

        # Command Queues - Explicitly initialize to prevent MagicMock infinite loops
        state.god_command_queue = deque()
        state.system_commands = []
        state.command_queue = MagicMock()
        state.command_queue.empty.return_value = True

        # Systems
        state.ma_manager = MagicMock()
        state.event_system = None
        state.commerce_system = None
        state.housing_system = MagicMock()
        state.crisis_monitor = None
        state.generational_wealth_audit = None
        state.settlement_system = MagicMock()
        state.ai_training_manager = None
        state.ai_trainer = None

        # Add missing optional fields that Orchestrator might access
        state.social_system = None
        state.sensory_system = None
        state.agent_registry = None
        state.saga_orchestrator = None
        state.monetary_ledger = None
        state.shareholder_registry = None
        state.taxation_system = None
        state.labor_market_analyzer = None
        state.public_manager = None
        state.currency_holders = []
        state.stress_scenario_config = None
        state.escrow_agent = None
        state.registry = None

        # Fix format issue
        from modules.simulation.dtos.api import MoneySupplyDTO
        state.calculate_total_money = MagicMock(return_value=MoneySupplyDTO(1000, 0))
        state.baseline_money_supply = 1000.0

        return state

    @pytest.fixture
    def orchestrator(self, mock_world_state):
        processor = MagicMock()

        # Patch the phases classes to return mocks
        with patch('simulation.orchestration.tick_orchestrator.Phase0_PreSequence') as MockPhase0, \
             patch('simulation.orchestration.tick_orchestrator.Phase_Production') as MockPhaseProd, \
             patch('simulation.orchestration.tick_orchestrator.Phase1_Decision') as MockPhase1, \
             patch('simulation.orchestration.tick_orchestrator.Phase_Bankruptcy') as MockPhaseBankruptcy, \
             patch('simulation.orchestration.tick_orchestrator.Phase_SystemicLiquidation') as MockPhaseLiquidation, \
             patch('simulation.orchestration.tick_orchestrator.Phase2_Matching') as MockPhase2, \
             patch('simulation.orchestration.tick_orchestrator.Phase3_Transaction') as MockPhase3, \
             patch('simulation.orchestration.tick_orchestrator.Phase_Consumption') as MockPhaseConsumption, \
             patch('simulation.orchestration.tick_orchestrator.Phase5_PostSequence') as MockPhase5:

             # Configure mocks to return the state passed to execute
             def side_effect(state):
                 return state

             MockPhase0.return_value.execute.side_effect = side_effect
             MockPhaseProd.return_value.execute.side_effect = side_effect
             MockPhase1.return_value.execute.side_effect = side_effect
             MockPhaseBankruptcy.return_value.execute.side_effect = side_effect
             MockPhaseLiquidation.return_value.execute.side_effect = side_effect
             MockPhase2.return_value.execute.side_effect = side_effect
             MockPhase3.return_value.execute.side_effect = side_effect
             MockPhaseConsumption.return_value.execute.side_effect = side_effect
             MockPhase5.return_value.execute.side_effect = side_effect

             orch = TickOrchestrator(mock_world_state, processor)

             # Store mock phases on the orchestrator instance for access in tests
             orch.mock_phases = {
                 'Phase0': MockPhase0.return_value,
                 'PhaseProduction': MockPhaseProd.return_value,
                 'Phase1': MockPhase1.return_value,
                 'PhaseBankruptcy': MockPhaseBankruptcy.return_value,
                 'PhaseLiquidation': MockPhaseLiquidation.return_value,
                 'Phase2': MockPhase2.return_value,
                 'Phase3': MockPhase3.return_value,
                 'PhaseConsumption': MockPhaseConsumption.return_value,
                 'Phase5': MockPhase5.return_value,
             }

             return orch

    def test_run_tick_executes_phases(self, orchestrator, mock_world_state):
        # Act
        orchestrator.run_tick()

        # Assertions - Check if phases were executed in order
        orchestrator.mock_phases['Phase0'].execute.assert_called_once()
        orchestrator.mock_phases['PhaseProduction'].execute.assert_called_once()
        orchestrator.mock_phases['Phase1'].execute.assert_called_once()
        orchestrator.mock_phases['PhaseBankruptcy'].execute.assert_called_once()
        orchestrator.mock_phases['PhaseLiquidation'].execute.assert_called_once()
        orchestrator.mock_phases['Phase2'].execute.assert_called_once()
        orchestrator.mock_phases['Phase3'].execute.assert_called_once()
        orchestrator.mock_phases['PhaseConsumption'].execute.assert_called_once()
        orchestrator.mock_phases['Phase5'].execute.assert_called_once()

        # Verify state time incremented
        assert mock_world_state.time == 1
