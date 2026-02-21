import pytest
from unittest.mock import MagicMock, call, ANY
from typing import List

from modules.finance.transaction.engine import (
    LedgerEngine,
    TransactionValidator,
    TransactionExecutor,
    SimpleTransactionLedger
)
from modules.finance.transaction.api import (
    TransactionDTO,
    TransactionResultDTO,
    IAccountAccessor,
    ITransactionParticipant,
    InvalidAccountError,
    InsufficientFundsError,
    NegativeAmountError,
    ExecutionError,
    ValidationError
)
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_accessor():
    return MagicMock(spec=IAccountAccessor)

@pytest.fixture
def mock_ledger():
    return MagicMock(spec=SimpleTransactionLedger)

@pytest.fixture
def mock_clock():
    return MagicMock(return_value=123.0)

@pytest.fixture
def validator(mock_accessor):
    return TransactionValidator(mock_accessor)

@pytest.fixture
def executor(mock_accessor):
    return TransactionExecutor(mock_accessor)

@pytest.fixture
def engine(validator, executor, mock_ledger, mock_clock):
    return LedgerEngine(validator, executor, mock_ledger, mock_clock)

# ==============================================================================
# Validator Tests
# ==============================================================================

def test_validator_success(validator, mock_accessor):
    tx = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test")

    mock_accessor.exists.return_value = True
    participant_a = MagicMock(spec=ITransactionParticipant)
    participant_a.get_balance.return_value = 200
    mock_accessor.get_participant.return_value = participant_a

    validator.validate(tx)
    # Should not raise

def test_validator_negative_amount(validator):
    tx = TransactionDTO("tx1", "A", "B", -10, DEFAULT_CURRENCY, "test")
    with pytest.raises(NegativeAmountError):
        validator.validate(tx)

def test_validator_invalid_type(validator):
    tx = TransactionDTO("tx1", "A", "B", 10.5, DEFAULT_CURRENCY, "test") # Float!
    with pytest.raises(ValidationError):
        validator.validate(tx)

def test_validator_account_not_exists(validator, mock_accessor):
    tx = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test")
    mock_accessor.exists.side_effect = [True, False] # B doesn't exist

    with pytest.raises(InvalidAccountError):
        validator.validate(tx)

def test_validator_insufficient_funds(validator, mock_accessor):
    tx = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test")

    mock_accessor.exists.return_value = True
    participant_a = MagicMock(spec=ITransactionParticipant)
    participant_a.get_balance.return_value = 50
    participant_a.allows_overdraft = False
    mock_accessor.get_participant.return_value = participant_a

    with pytest.raises(InsufficientFundsError):
        validator.validate(tx)

# ==============================================================================
# Executor Tests
# ==============================================================================

def test_executor_success(executor, mock_accessor):
    tx = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test")

    participant_a = MagicMock(spec=ITransactionParticipant)
    participant_b = MagicMock(spec=ITransactionParticipant)

    def get_participant(account_id):
        if account_id == "A": return participant_a
        if account_id == "B": return participant_b
        return None
    mock_accessor.get_participant.side_effect = get_participant

    executor.execute(tx)

    participant_a.withdraw.assert_called_once_with(100, DEFAULT_CURRENCY, memo=ANY)
    participant_b.deposit.assert_called_once_with(100, DEFAULT_CURRENCY, memo=ANY)

def test_executor_rollback_success(executor, mock_accessor):
    """Test that if deposit fails, withdrawal is rolled back."""
    tx = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test")

    participant_a = MagicMock(spec=ITransactionParticipant)
    participant_b = MagicMock(spec=ITransactionParticipant)
    participant_b.deposit.side_effect = Exception("Deposit Failed")

    def get_participant(account_id):
        if account_id == "A": return participant_a
        if account_id == "B": return participant_b
        return None
    mock_accessor.get_participant.side_effect = get_participant

    with pytest.raises(ExecutionError, match="Deposit failed"):
        executor.execute(tx)

    participant_a.withdraw.assert_called_once()
    participant_b.deposit.assert_called_once()
    participant_a.deposit.assert_called_once_with(100, DEFAULT_CURRENCY, memo=ANY) # Rollback

def test_executor_critical_rollback_failure(executor, mock_accessor):
    """Test critical failure if rollback also fails."""
    tx = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test")

    participant_a = MagicMock(spec=ITransactionParticipant)
    participant_b = MagicMock(spec=ITransactionParticipant)
    participant_b.deposit.side_effect = Exception("Deposit Failed")
    participant_a.deposit.side_effect = Exception("Rollback Failed") # Rollback fails!

    def get_participant(account_id):
        if account_id == "A": return participant_a
        if account_id == "B": return participant_b
        return None
    mock_accessor.get_participant.side_effect = get_participant

    with pytest.raises(ExecutionError, match="CRITICAL: Rollback failed"):
        executor.execute(tx)

# ==============================================================================
# Engine Tests
# ==============================================================================

def test_process_transaction_success(engine, mock_ledger, mock_accessor):
    # Setup Accessor for validation
    mock_accessor.exists.return_value = True
    participant = MagicMock()
    participant.get_balance.return_value = 1000 # Sufficient funds
    participant.allows_overdraft = False
    mock_accessor.get_participant.return_value = participant

    tx_result = engine.process_transaction("A", "B", 100, DEFAULT_CURRENCY, "test")

    assert tx_result.status == 'COMPLETED', f"Failed with message: {tx_result.message}"
    assert tx_result.timestamp == 123.0
    mock_ledger.record.assert_called_once()

def test_process_transaction_validation_fail(engine, mock_ledger, validator):
    validator.validate = MagicMock(side_effect=ValidationError("Invalid"))

    tx_result = engine.process_transaction("A", "B", 100, DEFAULT_CURRENCY, "test")

    assert tx_result.status == 'FAILED'
    assert "Invalid" in tx_result.message
    mock_ledger.record.assert_called_once()

def test_process_batch_atomicity(engine, mock_ledger, executor):
    """Test that if 2nd transaction fails, 1st is rolled back."""
    tx1 = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test1")
    tx2 = TransactionDTO("tx2", "C", "D", 100, DEFAULT_CURRENCY, "test2") # Will fail

    # Mock executor: tx1 succeeds, tx2 fails
    def execute_side_effect(tx):
        if tx.transaction_id == "tx1": return
        if tx.transaction_id == "tx2": raise ExecutionError("Exec Fail")
        if "rollback" in tx.transaction_id: return # Rollback succeeds
        raise ValueError(f"Unknown tx: {tx.transaction_id}")

    executor.execute = MagicMock(side_effect=execute_side_effect)
    # Re-assign executor to engine because we mocked the instance method
    engine.executor = executor

    # Validation passes for all
    engine.validator.validate = MagicMock()

    results = engine.process_batch([tx1, tx2])

    assert len(results) == 2
    assert results[0].status == 'FAILED' # Was rolled back
    assert "Rolled back" in results[0].message
    assert results[1].status == 'CRITICAL_FAILURE' # Execution failed
    assert "Exec Fail" in results[1].message

    # Check calls
    # Execute tx1
    # Execute tx2 -> Fail
    # Execute rollback_tx1
    executor.execute.assert_has_calls([
        call(tx1),
        call(tx2),
        call(ANY) # Rollback call
    ])
    assert "rollback_tx1" in executor.execute.call_args_list[2][0][0].transaction_id

def test_process_batch_rollback_failure(engine, mock_ledger, executor):
    """Test critical log if rollback fails during batch failure."""
    tx1 = TransactionDTO("tx1", "A", "B", 100, DEFAULT_CURRENCY, "test1")
    tx2 = TransactionDTO("tx2", "C", "D", 100, DEFAULT_CURRENCY, "test2")

    # Mock executor: tx1 succeeds, tx2 fails, rollback_tx1 fails
    def execute_side_effect(tx):
        if tx.transaction_id == "tx1": return
        if tx.transaction_id == "tx2": raise ExecutionError("Exec Fail")
        if "rollback" in tx.transaction_id: raise ExecutionError("Rollback Fail")
        raise ValueError(f"Unknown tx: {tx.transaction_id}")

    executor.execute = MagicMock(side_effect=execute_side_effect)
    engine.executor = executor
    engine.validator.validate = MagicMock()

    # We expect this to run but log CRITICAL.
    # The result status should still reflect failure.
    results = engine.process_batch([tx1, tx2])

    assert len(results) == 2
    assert results[0].status == 'FAILED'
    assert results[1].status == 'CRITICAL_FAILURE'

    # Verify rollback was attempted
    assert executor.execute.call_count == 3
