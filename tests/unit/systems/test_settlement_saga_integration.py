import pytest
from unittest.mock import MagicMock
from modules.finance.sagas.orchestrator import SagaOrchestrator
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.saga_handler import HousingTransactionSagaHandler

class TestSettlementSagaIntegration:
    @pytest.fixture
    def mock_simulation_state(self):
        sim = MagicMock()
        # Mock Simulation Dependencies
        sim.settlement_system = MagicMock()
        sim.housing_service = MagicMock()
        sim.markets = {"loan": MagicMock()}
        sim.agents = {}
        sim.time = 100
        sim.config_module = MagicMock()
        sim.config_module.TICKS_PER_YEAR = 100
        sim.bank = MagicMock()
        return sim

    def test_process_sagas_integration_initiated_to_credit_check(self, mock_simulation_state):
        """
        Tests that SagaOrchestrator correctly orchestrates the Real HousingTransactionSagaHandler
        to transition a saga from INITIATED to CREDIT_CHECK.
        """
        # 1. Setup Settlement System & Orchestrator
        settlement = SettlementSystem()
        orchestrator = SagaOrchestrator()

        # Wire up circular dependency (Handler needs access to SettlementSystem)
        mock_simulation_state.settlement_system = settlement

        # 2. Setup a Saga
        saga_id = "saga-integration-1"
        saga = {
            "saga_id": saga_id,
            "saga_type": "HOUSING_TRANSACTION",
            "status": "INITIATED",
            "current_step": 0,
            "buyer_id": 1,
            "seller_id": 2,
            "property_id": 101,
            "offer_price": 100000.0,
            "down_payment_amount": 20000.0,
            "last_processed_tick": 99, # To ensure it processes
            "loan_application": {"mock": "data"} # Required by handler
        }
        orchestrator.submit_saga(saga)

        # 3. Setup Dependencies for Handler
        # Mock agents
        buyer = MagicMock()
        buyer.is_active = True
        buyer.current_wage = 100.0
        buyer.get_balance.return_value = 100000.0

        seller = MagicMock()
        seller.is_active = True

        mock_simulation_state.agents = {1: buyer, 2: seller}

        # Mock Housing Service
        mock_simulation_state.housing_service.lock_asset.return_value = True

        # Mock Loan Market
        mock_simulation_state.markets["loan"].stage_mortgage_application.return_value = "loan_staged_1"

        # Mock Bank (for debt calculation)
        mock_simulation_state.bank.get_debt_status.return_value = {'loans': []}

        # 4. Run
        orchestrator.simulation_state = mock_simulation_state
        orchestrator.process_sagas()

        # 5. Verify Saga Transition
        assert saga_id in orchestrator.active_sagas
        updated_saga = orchestrator.active_sagas[saga_id]

        # Should transition to CREDIT_CHECK
        assert updated_saga["status"] == "CREDIT_CHECK"
        assert updated_saga["staged_loan_id"] == "loan_staged_1"
        assert updated_saga["last_processed_tick"] == 100

        # Verify side effects
        mock_simulation_state.housing_service.lock_asset.assert_called_with(101, saga_id)
        mock_simulation_state.markets["loan"].stage_mortgage_application.assert_called_once()

    def test_process_sagas_integration_cancellation(self, mock_simulation_state):
        """
        Tests that if a participant is inactive, SettlementSystem cancels the saga
        and triggers compensation (using the real handler's compensate logic).
        """
        # 1. Setup Settlement System & Orchestrator
        settlement = SettlementSystem()
        orchestrator = SagaOrchestrator()

        mock_simulation_state.settlement_system = settlement

        # 2. Setup a Saga (in CREDIT_CHECK state)
        saga_id = "saga-integration-cancel"
        saga = {
            "saga_id": saga_id,
            "status": "CREDIT_CHECK",
            "buyer_id": 1,
            "seller_id": 2,
            "property_id": 101,
            "staged_loan_id": "loan_staged_x",
            "last_processed_tick": 99
        }
        orchestrator.submit_saga(saga)

        # 3. Setup Dependencies
        # Buyer is DEAD/Inactive
        buyer = MagicMock()
        buyer.is_active = False

        seller = MagicMock()
        seller.is_active = True

        mock_simulation_state.agents = {1: buyer, 2: seller}

        # Mock Loan Market for voiding
        mock_simulation_state.markets["loan"].void_staged_application.return_value = True

        # 4. Run
        orchestrator.simulation_state = mock_simulation_state
        orchestrator.process_sagas()

        # 5. Verify Cancellation
        # Saga should be removed from active_sagas
        assert saga_id not in orchestrator.active_sagas

        # Check logs/mock calls to verify compensation was attempted
        mock_simulation_state.markets["loan"].void_staged_application.assert_called_with("loan_staged_x")
