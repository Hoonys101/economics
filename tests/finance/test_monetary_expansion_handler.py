import unittest
from unittest.mock import MagicMock, patch
from modules.finance.kernel.ledger import MonetaryLedger
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.dtos.api import SimulationState, DecisionContext
from simulation.models import Transaction

class TestMonetaryExpansionWarning(unittest.TestCase):

    def setUp(self):
        self.config_module = MagicMock()
        self.transaction_log = []
        self.time_provider = MagicMock()
        self.time_provider.time = 100

        self.ledger = MonetaryLedger(
            transaction_log=self.transaction_log,
            time_provider=self.time_provider
        )

        self.processor = TransactionProcessor(config_module=self.config_module)

        # Mock SimulationState
        self.state = MagicMock(spec=SimulationState)
        self.state.agents = {}
        self.state.inactive_agents = {}
        self.state.logger = MagicMock()
        self.state.time = 100
        self.state.transactions = []
        self.state.settlement_system = MagicMock()
        self.state.stock_market = MagicMock()
        self.state.real_estate_units = {}
        self.state.market_data = MagicMock()
        self.state.shareholder_registry = MagicMock()
        self.state.primary_government = MagicMock()
        self.state.estate_registry = MagicMock()

    def test_repro_warning(self):
        # 1. Record monetary expansion
        self.ledger.record_monetary_expansion(
            amount_pennies=1000,
            source="test_source"
        )

        # Get the generated transaction
        tx = self.transaction_log[0]

        # Verify transaction type
        self.assertEqual(tx.transaction_type, "monetary_expansion")

        # Verify metadata
        self.assertTrue(tx.metadata.get("executed"))
        self.assertTrue(tx.metadata.get("is_audit"))

        # 2. Execute via Processor
        # We expect NO warning now
        self.processor.execute(self.state, transactions=[tx])

        # 3. Assert Warning NOT Logged
        # We check that the specific warning was NOT logged
        calls = self.state.logger.warning.call_args_list
        warning_messages = [str(call[0][0]) for call in calls]

        self.assertNotIn(
            "No handler for tx type: monetary_expansion",
            warning_messages,
            f"Found warning: {warning_messages}"
        )
        print("Success: Warning suppressed as expected.")

if __name__ == "__main__":
    unittest.main()
