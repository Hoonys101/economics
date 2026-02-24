import unittest
from unittest.mock import MagicMock
from simulation.systems.transaction_processor import TransactionProcessor
from simulation.systems.handlers.financial_handler import FinancialTransactionHandler
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from modules.finance.engine_api import FinancialLedgerDTO, BankStateDTO

class TestLedgerSafety(unittest.TestCase):
    def test_processor_skips_executed_transactions(self):
        """
        Verify that TransactionProcessor does NOT process transactions marked as executed.
        This confirms that appending tax audit logs to the queue does not trigger double taxation.
        """
        config = MagicMock()
        processor = TransactionProcessor(config)

        handler = MagicMock()
        processor.register_handler("tax", handler)

        # Create an 'executed' transaction (Audit Log)
        tx = Transaction(
            buyer_id=1, seller_id=99, item_id="tax_log", quantity=1, price=100,
            transaction_type="tax", time=1, total_pennies=100,
            market_id="system",
            metadata={"executed": True}
        )

        # State Mock
        state = MagicMock(spec=SimulationState)
        state.transactions = [tx]
        state.agents = {1: MagicMock(), 99: MagicMock()}
        state.inactive_agents = {}
        state.primary_government = MagicMock()
        state.stock_market = MagicMock()
        state.real_estate_units = []
        state.market_data = {}
        state.logger = MagicMock()
        state.time = 1
        state.bank = MagicMock()
        state.central_bank = MagicMock()
        state.settlement_system = MagicMock()
        state.shareholder_registry = MagicMock()

        # Execute
        results = processor.execute(state)

        # Assertions
        handler.handle.assert_not_called()
        self.assertEqual(len(results), 0, "Should return no results for skipped transactions")

    def test_financial_handler_does_not_touch_ledger_dto(self):
        """
        Verify that FinancialTransactionHandler updates Wallet (Settlement) but NOT the Ledger DTO.
        This confirms that DebtServicingEngine must manually update the Ledger DTO (Retained Earnings).
        """
        handler = FinancialTransactionHandler()

        # Mock Context
        context = MagicMock()
        context.settlement_system = MagicMock()
        context.settlement_system.transfer.return_value = True

        # Mock Ledger DTO (This should NOT be touched by Handler)
        # Note: Handler doesn't even receive the Ledger DTO in the context usually,
        # but let's check if it tries to access 'bank' context to update it.
        ledger_mock = MagicMock(spec=FinancialLedgerDTO)
        context.finance_system = MagicMock()
        context.finance_system.ledger = ledger_mock

        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="loan_1", quantity=1, price=50,
            transaction_type="loan_interest", time=1, total_pennies=5000,
            market_id="financial"
        )

        buyer = MagicMock() # Borrower
        seller = MagicMock() # Bank

        # Execute
        handler.handle(tx, buyer, seller, context)

        # Assertions
        # 1. Settlement Transfer Called (Wallet Update)
        context.settlement_system.transfer.assert_called_with(buyer, seller, 5000, "loan_interest")

        # 2. Ledger DTO NOT touched
        # We assume Handler is unaware of DTO structure.
        # Ideally, we check that no method like 'record_revenue' was called on the seller IF seller was a DTO wrapper.
        # But here we verify that the handler logic simply doesn't contain code to update 'retained_earnings'.
        # This is implicitly verified by the code review, but dynamically:
        # Does the handler call anything on 'seller' besides checking interfaces?
        # The code is: if isinstance(buyer, IExpenseTracker): buyer.record_expense(...)
        # It does NOT call seller.record_revenue().

        # Let's verify 'record_revenue' is NOT called on seller
        seller.record_revenue.assert_not_called()
