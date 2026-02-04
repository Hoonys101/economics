import pytest
from unittest.mock import Mock, MagicMock

from modules.finance.transaction.api import (
    TransactionDTO,
    InsufficientFundsError,
    InvalidAccountError,
    NegativeAmountError,
    ExecutionError,
    IAccountAccessor,
    ITransactionLedger
)
from modules.finance.transaction.engine import (
    TransactionValidator,
    TransactionExecutor,
    TransactionEngine
)
from modules.finance.wallet.api import IWallet
from modules.finance.transaction.adapter import RegistryAccountAccessor
from modules.system.api import IAgentRegistry

# ==============================================================================
# Validator Tests
# ==============================================================================

def test_validator_success():
    mock_accessor = Mock(spec=IAccountAccessor)
    mock_accessor.exists.return_value = True
    mock_wallet = Mock(spec=IWallet)
    mock_wallet.get_balance.return_value = 100.0
    mock_accessor.get_wallet.return_value = mock_wallet

    validator = TransactionValidator(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=50.0,
        currency="USD",
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
        amount=-10.0,
        currency="USD",
        description="test"
    )

    with pytest.raises(NegativeAmountError):
        validator.validate(dto)

def test_validator_insufficient_funds():
    mock_accessor = Mock(spec=IAccountAccessor)
    mock_accessor.exists.return_value = True
    mock_wallet = Mock(spec=IWallet)
    mock_wallet.get_balance.return_value = 10.0
    mock_accessor.get_wallet.return_value = mock_wallet

    validator = TransactionValidator(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=50.0,
        currency="USD",
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
        amount=50.0,
        currency="USD",
        description="test"
    )

    with pytest.raises(InvalidAccountError):
        validator.validate(dto)


# ==============================================================================
# Executor Tests
# ==============================================================================

def test_executor_success():
    mock_accessor = Mock(spec=IAccountAccessor)
    src_wallet = Mock(spec=IWallet)
    dst_wallet = Mock(spec=IWallet)

    def get_wallet_side_effect(id):
        if id == "src": return src_wallet
        if id == "dst": return dst_wallet
        raise InvalidAccountError()

    mock_accessor.get_wallet.side_effect = get_wallet_side_effect

    executor = TransactionExecutor(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=50.0,
        currency="USD",
        description="test"
    )

    executor.execute(dto)

    src_wallet.subtract.assert_called_once()
    dst_wallet.add.assert_called_once()

def test_executor_failure():
    mock_accessor = Mock(spec=IAccountAccessor)
    src_wallet = Mock(spec=IWallet)
    # Simulate failure during subtract
    src_wallet.subtract.side_effect = Exception("DB Error")
    mock_accessor.get_wallet.return_value = src_wallet

    executor = TransactionExecutor(mock_accessor)

    dto = TransactionDTO(
        transaction_id="1",
        source_account_id="src",
        destination_account_id="dst",
        amount=50.0,
        currency="USD",
        description="test"
    )

    with pytest.raises(ExecutionError):
        executor.execute(dto)


# ==============================================================================
# Engine Tests
# ==============================================================================

def test_engine_process_transaction_success():
    mock_validator = Mock()
    mock_executor = Mock()
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    result = engine.process_transaction("src", "dst", 100.0, "USD", "test")

    assert result['status'] == 'COMPLETED'
    mock_validator.validate.assert_called_once()
    mock_executor.execute.assert_called_once()
    mock_ledger.record.assert_called_once()
    assert mock_ledger.record.call_args[0][0]['status'] == 'COMPLETED'

def test_engine_process_transaction_validation_fail():
    mock_validator = Mock()
    mock_validator.validate.side_effect = InsufficientFundsError("Not enough money")
    mock_executor = Mock()
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    result = engine.process_transaction("src", "dst", 100.0, "USD", "test")

    assert result['status'] == 'FAILED'
    assert "Not enough money" in result['message']
    mock_executor.execute.assert_not_called()
    mock_ledger.record.assert_called_once()
    assert mock_ledger.record.call_args[0][0]['status'] == 'FAILED'

def test_engine_process_transaction_execution_fail():
    mock_validator = Mock()
    mock_executor = Mock()
    mock_executor.execute.side_effect = ExecutionError("Critical fail")
    mock_ledger = Mock(spec=ITransactionLedger)

    engine = TransactionEngine(mock_validator, mock_executor, mock_ledger)

    result = engine.process_transaction("src", "dst", 100.0, "USD", "test")

    assert result['status'] == 'CRITICAL_FAILURE'
    assert "Critical fail" in result['message']
    mock_ledger.record.assert_called_once()
    assert mock_ledger.record.call_args[0][0]['status'] == 'CRITICAL_FAILURE'

# ==============================================================================
# Adapter Tests
# ==============================================================================

def test_adapter_registry_accessor():
    mock_registry = Mock(spec=IAgentRegistry)
    mock_agent = Mock()
    mock_wallet = Mock(spec=IWallet)
    mock_agent.wallet = mock_wallet

    mock_registry.get_agent.return_value = mock_agent

    accessor = RegistryAccountAccessor(mock_registry)

    # Test get_wallet with digit string, expect int conversion
    wallet = accessor.get_wallet("123")
    assert wallet == mock_wallet
    mock_registry.get_agent.assert_called_with(123)

    # Test exists
    assert accessor.exists("123")

    # Test not found
    mock_registry.get_agent.return_value = None
    assert not accessor.exists("999")
    with pytest.raises(InvalidAccountError):
        accessor.get_wallet("999")
