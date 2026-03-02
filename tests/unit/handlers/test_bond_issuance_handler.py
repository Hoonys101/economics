import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.handlers.bond_issuance import BondIssuanceHandler
from modules.finance.api import BondIssuanceRequestDTO, IBondMarketSystem
from modules.finance.transaction.api import ILedgerEngine, TransactionResultDTO
from modules.system.api import DEFAULT_CURRENCY

def test_bond_issuance_handler_success():
    mock_bond_system = Mock(spec=IBondMarketSystem)
    mock_bond_system.issue_bond.return_value = True

    mock_ledger = Mock(spec=ILedgerEngine)
    mock_ledger.process_transaction.return_value = TransactionResultDTO(
        transaction=Mock(), status='COMPLETED', message="OK", timestamp=0.0
    )

    handler = BondIssuanceHandler(mock_bond_system, mock_ledger)

    request = BondIssuanceRequestDTO(
        issuer_id=1, buyer_id=2, face_value=100, issue_price=90,
        quantity=10, coupon_rate=0.05, maturity_tick=100
    )

    result = handler.execute(request, None)

    assert result is True
    # Verify Payment
    mock_ledger.process_transaction.assert_called_once()
    args = mock_ledger.process_transaction.call_args[1]
    assert args['source_account_id'] == "2"
    assert args['destination_account_id'] == "1"
    assert args['amount'] == 900 # 90 * 10

    # Verify Asset Creation
    mock_bond_system.issue_bond.assert_called_with(request)

def test_bond_issuance_handler_payment_fail():
    mock_bond_system = Mock(spec=IBondMarketSystem)
    mock_ledger = Mock(spec=ILedgerEngine)
    mock_ledger.process_transaction.return_value = TransactionResultDTO(
        transaction=Mock(), status='FAILED', message="No Funds", timestamp=0.0
    )

    handler = BondIssuanceHandler(mock_bond_system, mock_ledger)
    request = BondIssuanceRequestDTO(1, 2, 100, 90, 10, 0.05, 100)

    with pytest.raises(ValueError, match="Bond Issuance Payment Failed"):
        handler.execute(request, None)

    mock_bond_system.issue_bond.assert_not_called()

def test_bond_issuance_handler_asset_fail_rollback():
    mock_bond_system = Mock(spec=IBondMarketSystem)
    mock_bond_system.issue_bond.return_value = False # Fail asset creation

    mock_ledger = Mock(spec=ILedgerEngine)
    mock_ledger.process_transaction.side_effect = [
        TransactionResultDTO(Mock(), 'COMPLETED', "OK", 0.0), # Payment
        TransactionResultDTO(Mock(), 'COMPLETED', "OK", 0.0)  # Rollback
    ]

    handler = BondIssuanceHandler(mock_bond_system, mock_ledger)
    request = BondIssuanceRequestDTO(1, 2, 100, 90, 10, 0.05, 100)

    with pytest.raises(ValueError, match="Bond Market System returned False"):
        handler.execute(request, None)

    # Verify Payment and Rollback
    assert mock_ledger.process_transaction.call_count == 2
    # Check Rollback call
    # Note: call_args_list is a list of Call objects. Call objects are tuple-like.
    rollback_call = mock_ledger.process_transaction.call_args_list[1]
    rollback_args = rollback_call.kwargs
    assert rollback_args['source_account_id'] == "1" # Issuer returns money
    assert rollback_args['destination_account_id'] == "2"

def test_bond_issuance_handler_rollback_manual():
    mock_bond_system = Mock(spec=IBondMarketSystem)
    mock_bond_system.issue_bond.return_value = True
    mock_bond_system.cancel_bond.return_value = True

    mock_ledger = Mock(spec=ILedgerEngine)
    # 1. Execution payment
    # 2. Rollback reverse payment
    mock_ledger.process_transaction.return_value = TransactionResultDTO(
        transaction=Mock(), status='COMPLETED', message="OK", timestamp=0.0
    )

    handler = BondIssuanceHandler(mock_bond_system, mock_ledger)
    request = BondIssuanceRequestDTO(
        issuer_id=1, buyer_id=2, face_value=100, issue_price=90,
        quantity=10, coupon_rate=0.05, maturity_tick=100,
        transaction_id="TX_ROLLBACK_TEST"
    )

    # 1. Execute
    handler.execute(request, None)
    
    # 2. Rollback
    result = handler.rollback("TX_ROLLBACK_TEST", None)

    assert result is True
    assert mock_ledger.process_transaction.call_count == 2
    assert mock_bond_system.cancel_bond.call_count == 1
    
    # Verify rollback args
    rollback_call = mock_ledger.process_transaction.call_args_list[1]
    assert rollback_call.kwargs['source_account_id'] == "1"
    assert rollback_call.kwargs['destination_account_id'] == "2"
    assert rollback_call.kwargs['amount'] == 900
    
    mock_bond_system.cancel_bond.assert_called_with("BOND_TX_ROLLBACK_TEST")
