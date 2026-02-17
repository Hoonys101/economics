import pytest
from unittest.mock import MagicMock
from typing import List
from modules.finance.transaction.api import (
    TransactionDTO,
    TransactionResultDTO,
    ITransactionExecutor,
    ExecutionError,
    ITransactionValidator,
    ITransactionLedger
)
from modules.finance.transaction.engine import TransactionEngine

class MockExecutor:
    def __init__(self):
        self.executed = []
        self.fail_on_id = None

    def execute(self, transaction: TransactionDTO):
        if self.fail_on_id and transaction.transaction_id == self.fail_on_id:
            raise ExecutionError(f"Simulated failure for {transaction.transaction_id}")
        self.executed.append(transaction)

def test_process_batch_rollback_integrity():
    """
    Verifies that if a transaction in a batch fails, previous successful transactions
    are rolled back to maintain zero-sum integrity.
    """
    # Setup
    mock_validator = MagicMock(spec=ITransactionValidator)
    mock_ledger = MagicMock(spec=ITransactionLedger)
    executor = MockExecutor()

    engine = TransactionEngine(
        validator=mock_validator,
        executor=executor, # type: ignore
        ledger=mock_ledger
    )

    # Create batch of 3 transactions
    # 1. Valid
    # 2. Fails
    # 3. Valid (but shouldn't run)
    tx1 = TransactionDTO("tx1", "AccountA", "AccountB", 100, "USD", "Test 1")
    tx2 = TransactionDTO("tx2", "AccountB", "AccountC", 200, "USD", "Test 2")
    tx3 = TransactionDTO("tx3", "AccountC", "AccountA", 300, "USD", "Test 3")

    executor.fail_on_id = "tx2"

    # Execute Batch
    results = engine.process_batch([tx1, tx2, tx3])

    # --- Verification ---

    # 1. Check Result Statuses
    # All should be reported as FAILED because it's an atomic batch
    assert len(results) == 3
    assert results[0].status == 'FAILED', "First transaction should be marked failed due to batch failure"
    # The failed transaction might be marked FAILED or CRITICAL_FAILURE depending on implementation specifics
    assert results[1].status in ('FAILED', 'CRITICAL_FAILURE'), "Second transaction failed"

    # 2. Check Execution Trace
    executed_ids = [t.transaction_id for t in executor.executed]

    # tx1 should have executed
    assert "tx1" in executed_ids, "tx1 should have executed initially"

    # tx2 failed before appending to `executed` list in our mock
    assert "tx2" not in executed_ids, "tx2 failed execution"

    # tx3 should NOT have executed
    assert "tx3" not in executed_ids, "tx3 should not have executed"

    # tx1 should have been rolled back
    rollback_id = "rollback_tx1"
    assert rollback_id in executed_ids, "tx1 should have been rolled back"

    # 3. Verify Rollback Details (Zero-Sum Integrity)
    rollback_tx = [t for t in executor.executed if t.transaction_id == rollback_id][0]
    assert rollback_tx.source_account_id == "AccountB", "Rollback source should be original destination"
    assert rollback_tx.destination_account_id == "AccountA", "Rollback dest should be original source"
    assert rollback_tx.amount == 100, "Rollback amount should match"
    assert rollback_tx.currency == "USD", "Rollback currency should match"
