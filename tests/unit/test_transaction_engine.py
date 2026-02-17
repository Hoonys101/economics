import pytest
from unittest.mock import Mock, MagicMock, call

from modules.finance.transaction.api import (
    TransactionDTO,
    InsufficientFundsError,
    InvalidAccountError,
    NegativeAmountError,
    ExecutionError,
    IAccountAccessor,
    ITransactionLedger,
    ITransactionParticipant,
    ITransactionValidator,
    ITransactionExecutor
)
from modules.finance.transaction.engine import (
    TransactionValidator,
    TransactionExecutor,
    TransactionEngine
)
from modules.finance.transaction.adapter import RegistryAccountAccessor
from modules.finance.api import IFinancialAgent, IFinancialEntity
from modules.system.api import IAgentRegistry, DEFAULT_CURRENCY

# ==============================================================================
# Validator Tests
# ==============================================================================

def test_validator_success():
    mock_accessor = Mock(spec=IAccountAccessor)
    mock_accessor.exists.return_value = True
    mock_participant = Mock(spec=ITransactionParticipant)
    mock_participant.get_balance.return_value = 10000 # 100.00
    mock_participant.allows_overdraft = False
    mock_accessor.get_participant.return_value = mock_participant

    validator = TransactionValidator(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=5000, # 50.00
        currency=DEFAULT_CURRENCY,
        description="test"
    )

    # Should not raise
    validator.validate(dto)

def test_validator_negative_amount():
    mock_accessor = Mock(spec=IAccountAccessor)
    validator = TransactionValidator(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=-1000,
        currency=DEFAULT_CURRENCY,
        description="test"
    )

    with pytest.raises(NegativeAmountError):
        validator.validate(dto)

def test_validator_insufficient_funds():
    mock_accessor = Mock(spec=IAccountAccessor)
    mock_accessor.exists.return_value = True
    mock_participant = Mock(spec=ITransactionParticipant)
    mock_participant.get_balance.return_value = 1000 # 10.00
    mock_participant.allows_overdraft = False
    mock_accessor.get_participant.return_value = mock_participant

    validator = TransactionValidator(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=5000, # 50.00
        currency=DEFAULT_CURRENCY,
        description="test"
    )

    with pytest.raises(InsufficientFundsError):
        validator.validate(dto)

def test_validator_invalid_account():
    mock_accessor = Mock(spec=IAccountAccessor)
    mock_accessor.exists.side_effect = lambda id: id == "existing"

    validator = TransactionValidator(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="non_existing",
        destination_account_id="existing",
        amount=5000,
        currency=DEFAULT_CURRENCY,
        description="test"
    )

    with pytest.raises(InvalidAccountError):
        validator.validate(dto)


# ==============================================================================
# Executor Tests
# ==============================================================================

def test_executor_success():
    mock_accessor = Mock(spec=IAccountAccessor)
    src_participant = Mock(spec=ITransactionParticipant)
    dst_participant = Mock(spec=ITransactionParticipant)

    def get_participant_side_effect(id):
        if id == "src": return src_participant
        if id == "dst": return dst_participant
        raise InvalidAccountError()

    mock_accessor.get_participant.side_effect = get_participant_side_effect

    executor = TransactionExecutor(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=5000,
        currency=DEFAULT_CURRENCY,
        description="test"
    )

    executor.execute(dto)

    src_participant.withdraw.assert_called_once_with(5000, DEFAULT_CURRENCY, memo="Transfer to dst: test")
    dst_participant.deposit.assert_called_once_with(5000, DEFAULT_CURRENCY, memo="Transfer from src: test")

def test_executor_failure_rollback():
    mock_accessor = Mock(spec=IAccountAccessor)
    src_participant = Mock(spec=ITransactionParticipant)
    dst_participant = Mock(spec=ITransactionParticipant)

    def get_participant_side_effect(id):
        if id == "src": return src_participant
        if id == "dst": return dst_participant
        raise InvalidAccountError()

    mock_accessor.get_participant.side_effect = get_participant_side_effect

    # Simulate success withdraw, fail deposit
    dst_participant.deposit.side_effect = Exception("DB Error")

    executor = TransactionExecutor(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=5000,
        currency=DEFAULT_CURRENCY,
        description="test"
    )

    with pytest.raises(ExecutionError):
        executor.execute(dto)

    # Verify Rollback
    src_participant.withdraw.assert_called_once()
    dst_participant.deposit.assert_called_once()
    src_participant.deposit.assert_called_once_with(5000, DEFAULT_CURRENCY, memo="ROLLBACK: Failed transfer to dst")


# ==============================================================================
# Engine Tests
# ==============================================================================

def test_engine_process_transaction_success():
    mock_validator = Mock(spec=ITransactionValidator)
    mock_executor = Mock(spec=ITransactionExecutor)
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    result = engine.process_transaction("src", "dst", 10000, DEFAULT_CURRENCY, "test")

    assert result.status == 'COMPLETED'
    mock_validator.validate.assert_called_once()
    mock_executor.execute.assert_called_once()
    mock_ledger.record.assert_called_once()
    assert mock_ledger.record.call_args[0][0].status == 'COMPLETED'

def test_engine_process_transaction_validation_fail():
    mock_validator = Mock(spec=ITransactionValidator)
    mock_validator.validate.side_effect = InsufficientFundsError("Not enough money")
    mock_executor = Mock(spec=ITransactionExecutor)
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    result = engine.process_transaction("src", "dst", 10000, DEFAULT_CURRENCY, "test")

    assert result.status == 'FAILED'
    assert "Not enough money" in result.message
    mock_executor.execute.assert_not_called()
    mock_ledger.record.assert_called_once()
    assert mock_ledger.record.call_args[0][0].status == 'FAILED'

def test_engine_process_transaction_execution_fail():
    mock_validator = Mock(spec=ITransactionValidator)
    mock_executor = Mock(spec=ITransactionExecutor)
    mock_executor.execute.side_effect = ExecutionError("Critical fail")
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    result = engine.process_transaction("src", "dst", 10000, DEFAULT_CURRENCY, "test")

    assert result.status == 'CRITICAL_FAILURE'
    assert "Critical fail" in result.message
    mock_ledger.record.assert_called_once()
    assert mock_ledger.record.call_args[0][0].status == 'CRITICAL_FAILURE'

def test_engine_process_batch_success():
    mock_validator = Mock(spec=ITransactionValidator)
    mock_executor = Mock(spec=ITransactionExecutor)
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    tx1 = TransactionDTO("1", "src", "dst", 100, DEFAULT_CURRENCY, "t1")
    tx2 = TransactionDTO("2", "dst", "src", 50, DEFAULT_CURRENCY, "t2")

    results = engine.process_batch([tx1, tx2])

    assert len(results) == 2
    assert results[0].status == 'COMPLETED'
    assert results[1].status == 'COMPLETED'
    assert mock_executor.execute.call_count == 2
    assert mock_ledger.record.call_count == 2

def test_engine_process_batch_rollback():
    mock_validator = Mock(spec=ITransactionValidator)
    mock_executor = Mock(spec=ITransactionExecutor)
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    tx1 = TransactionDTO("1", "src", "dst", 100, DEFAULT_CURRENCY, "t1")
    tx2 = TransactionDTO("2", "dst", "src", 50, DEFAULT_CURRENCY, "t2")

    # Second transaction fails execution
    def execute_side_effect(tx):
        if tx.transaction_id == "2":
            raise ExecutionError("Fail")
        return None

    mock_executor.execute.side_effect = execute_side_effect

    results = engine.process_batch([tx1, tx2])

    assert len(results) == 2
    # Both should be marked failed (or one failed one critical)
    assert results[0].status == 'FAILED'
    assert results[1].status == 'CRITICAL_FAILURE' or results[1].status == 'FAILED'

    # Verify rollback called for tx1
    # Executor called for tx1 (exec), tx2 (fail), rollback_tx1 (exec)
    assert mock_executor.execute.call_count == 3

    # Check arguments of calls
    calls = mock_executor.execute.call_args_list
    assert calls[0][0][0].transaction_id == "1"
    assert calls[1][0][0].transaction_id == "2"
    assert calls[2][0][0].transaction_id == "rollback_1"

# ==============================================================================
# Adapter Tests
# ==============================================================================

def test_adapter_registry_accessor():
    mock_registry = Mock(spec=IAgentRegistry)
    mock_agent = Mock(spec=IFinancialAgent)
    mock_agent.get_balance.return_value = 1000

    mock_registry.get_agent.return_value = mock_agent

    accessor = RegistryAccountAccessor(mock_registry)

    # Test get_participant with digit string, expect int conversion
    participant = accessor.get_participant("123")
    assert participant.get_balance() == 1000
    mock_registry.get_agent.assert_called_with(123)

    # Test exists
    assert accessor.exists("123")
