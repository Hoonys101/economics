import pytest
from unittest.mock import MagicMock, Mock
from collections import deque
from simulation.orchestration.tick_orchestrator import TickOrchestrator
from simulation.dtos.api import SimulationState
from simulation.orchestration.api import IPhaseStrategy

class MockPhase(IPhaseStrategy):
    def __init__(self, action):
        self.action = action

    def execute(self, state: SimulationState) -> SimulationState:
        self.action(state)
        return state

class TestStateSynchronization:

    @pytest.fixture
    def world_state(self):
        ws = MagicMock()
        ws.time = 1
        ws.next_agent_id = 100
        ws.households = []
        ws.firms = []
        ws.agents = {}
        ws.markets = {}
        ws.effects_queue = []
        ws.inter_tick_queue = []
        ws.transactions = []
        ws.god_command_queue = deque()
        ws.system_commands = []
        ws.command_queue = None
        ws.inactive_agents = {}
        ws.real_estate_units = []
        ws.goods_data = {}
        # Mocks for other dependencies
        ws.bank = MagicMock()
        ws.central_bank = MagicMock()
        ws.government = MagicMock()
        ws.stock_market = MagicMock()
        ws.stock_tracker = MagicMock()
        ws.config_module = MagicMock()
        ws.tracker = MagicMock()
        ws.logger = MagicMock()
        ws.ai_training_manager = MagicMock()
        ws.ai_trainer = MagicMock()
        ws.settlement_system = MagicMock()
        return ws

    @pytest.fixture
    def action_processor(self):
        return MagicMock()

    def test_transient_queue_accumulation(self, world_state, action_processor):
        """
        Verify that multiple phases appending to transient queues result in
        accumulated data in WorldState due to the drain mechanism.
        """
        # Define actions for phases
        def action_a(state):
            state.effects_queue.append({"id": "A", "type": "effect"})
            state.transactions.append("tx_A")

        def action_b(state):
            state.effects_queue.append({"id": "B", "type": "effect"})
            state.transactions.append("tx_B")

        # Create Orchestrator
        orchestrator = TickOrchestrator(world_state, action_processor)

        # Inject Mock Phases
        orchestrator.phases = [
            MockPhase(action_a),
            MockPhase(action_b)
        ]

        # Override _finalize_tick to prevent errors on mock objects (if necessary)
        orchestrator._finalize_tick = MagicMock()

        # Run Tick
        orchestrator.run_tick()

        # Assertions
        assert len(world_state.effects_queue) == 2
        assert {"id": "A", "type": "effect"} in world_state.effects_queue
        assert {"id": "B", "type": "effect"} in world_state.effects_queue

        assert len(world_state.transactions) == 2
        assert "tx_A" in world_state.transactions
        assert "tx_B" in world_state.transactions

    def test_reassignment_guardrail(self, world_state, action_processor):
        """
        Verify that re-assigning the 'agents' collection raises a RuntimeError.
        """
        def action_bad(state):
            state.agents = {} # Re-assignment!

        orchestrator = TickOrchestrator(world_state, action_processor)
        orchestrator.phases = [MockPhase(action_bad)]

        with pytest.raises(RuntimeError, match="CRITICAL: 'agents' collection was re-assigned"):
            orchestrator.run_tick()
