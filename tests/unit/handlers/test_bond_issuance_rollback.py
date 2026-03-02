import pytest
from unittest.mock import MagicMock
from modules.finance.handlers.bond_issuance import BondIssuanceHandler
from modules.finance.api import BondIssuanceRequestDTO
from modules.finance.transaction.api import TransactionResultDTO, TransactionDTO

def test_bond_issuance_rollback_success():
    bond_market = MagicMock()
    ledger = MagicMock()
    handler = BondIssuanceHandler(bond_market, ledger)

    # Create request
    request = BondIssuanceRequestDTO(
        issuer_id="1", buyer_id="2", face_value=100, issue_price=100, quantity=10,
        coupon_rate=0.05, maturity_tick=10, transaction_id="test_tx"
    )

    # Mock ledger process to return success for both execute and rollback
    success_result = TransactionResultDTO(
        transaction=TransactionDTO("tx", "src", "dst", 1000, "USD", "desc"),
        status='COMPLETED', message="OK", timestamp=1.0
    )
    ledger.process_transaction.return_value = success_result

    # Mock bond market to return success
    bond_market.issue_bond.return_value = True
    bond_market.cancel_bond.return_value = True

    # Execute
    assert handler.execute(request, None) is True

    # Verify rollback
    assert handler.rollback("test_tx", None) is True
    bond_market.cancel_bond.assert_called_once_with("BOND_test_tx")
    assert ledger.process_transaction.call_count == 2
