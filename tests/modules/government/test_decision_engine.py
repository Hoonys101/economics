import pytest
from unittest.mock import MagicMock
from modules.government.engines.decision_engine import GovernmentDecisionEngine
from modules.government.api import IGovBrain, GovernmentStateDTO
from simulation.dtos.api import MarketSnapshotDTO
from modules.government.dtos import PolicyDecisionDTO, PolicyActionTag

class TestGovernmentDecisionEngine:

    @pytest.fixture
    def mock_brain(self):
        return MagicMock(spec=IGovBrain)

    @pytest.fixture
    def mock_config(self):
        return MagicMock()

    @pytest.fixture
    def engine(self, mock_config, mock_brain):
        return GovernmentDecisionEngine(mock_config, mock_brain)

    def test_decide_delegates_to_brain(self, engine, mock_brain):
        # Setup
        snapshot = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"total_trade_volume": 5000.0},
            housing=None,
            loan=None,
            labor=None
        )

        state = GovernmentStateDTO(
            treasury_balance=10000.0,
            current_tax_rates={"income_tax": 0.1},
            active_welfare_programs=[]
        )

        # Brain returns NEW state
        target_state = GovernmentStateDTO(
            treasury_balance=10000.0,
            current_tax_rates={"income_tax": 0.08, "corporate_tax": 0.18},
            active_welfare_programs=[]
        )
        mock_brain.evaluate_policies.return_value = target_state

        # Execute
        decision = engine.decide(state, snapshot, MagicMock())

        # Verify
        assert isinstance(decision, PolicyDecisionDTO)
        assert decision.status == "EXECUTED"
        assert decision.parameters["income_tax_rate"] == 0.08
        assert decision.parameters["corporate_tax_rate"] == 0.18

        # Verify Brain Call - We expect it was called with a Strict DTO, not Legacy.
        # So we check the call arg type.
        mock_brain.evaluate_policies.assert_called_once()
        args, _ = mock_brain.evaluate_policies.call_args
        arg_snapshot = args[0]

        # Verify it's not the Legacy DTO
        assert not isinstance(arg_snapshot, MarketSnapshotDTO)
        # Verify fields
        assert arg_snapshot.timestamp == 100
        assert arg_snapshot.total_trade_volume == 5000.0
