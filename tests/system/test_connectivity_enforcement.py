import pytest
from unittest.mock import MagicMock

from modules.finance.wallet.wallet import Wallet
from modules.agent_framework.components.inventory_component import InventoryComponent
from modules.finance.api import SystemicIntegrityError
from simulation.systems.settlement_system import FinancialSentry, InventorySentry, SettlementSystem
from simulation.systems.handlers.transfer_handler import DefaultTransferHandler
from simulation.models import Transaction

def test_financial_sentry_violation():
    wallet = Wallet(1, {})
    with pytest.raises(SystemicIntegrityError, match="Direct mutation of wallet balance is FORBIDDEN"):
        wallet.add(100)

    with pytest.raises(SystemicIntegrityError, match="Direct mutation of wallet balance is FORBIDDEN"):
        wallet.subtract(50)

    with FinancialSentry.unlocked():
        wallet.add(100)
        assert wallet.get_balance() == 100

def test_inventory_sentry_violation():
    inv = InventoryComponent("1")
    with pytest.raises(SystemicIntegrityError, match="Direct mutation of inventory is FORBIDDEN"):
        inv.add_item("wood", 10.0)

    with InventorySentry.unlocked():
        inv.add_item("wood", 10.0)
        assert inv.get_quantity("wood") == 10.0

    with pytest.raises(SystemicIntegrityError, match="Direct mutation of inventory is FORBIDDEN"):
        inv.remove_item("wood", 5.0)

def test_default_transfer_handler_m2_visibility():
    handler = DefaultTransferHandler()

    mock_ledger = MagicMock()
    mock_settlement = MagicMock()
    mock_settlement.monetary_ledger = mock_ledger

    mock_buyer = MagicMock()
    mock_buyer.id = 1
    mock_seller = MagicMock()
    mock_seller.id = 2

    def side_effect_is_m2(agent):
        if agent.id == 1:
            return True
        return False
    mock_settlement._is_m2_agent.side_effect = side_effect_is_m2

    mock_context = MagicMock()
    mock_context.settlement_system = mock_settlement

    # Transfer from M2 to Non-M2 (Contraction)
    tx_contraction = Transaction(
        buyer_id=1,
        seller_id=2,
        item_id="usd",
        quantity=1.0,
        price=10.0,
        total_pennies=1000,
        market_id="m",
        transaction_type="transfer",
        time=0,
        metadata={"memo": "loan_repayment"}
    )

    handler.handle(tx_contraction, mock_buyer, mock_seller, mock_context)
    mock_ledger.record_monetary_contraction.assert_called_once_with(1000, source="loan_repayment", currency="USD")
    mock_ledger.record_monetary_expansion.assert_not_called()

    mock_ledger.reset_mock()

    # Transfer from Non-M2 to M2 (Expansion)
    tx_expansion = Transaction(
        buyer_id=2,
        seller_id=1,
        item_id="usd",
        quantity=1.0,
        price=10.0,
        total_pennies=500,
        market_id="m",
        transaction_type="transfer",
        time=0,
        metadata={"memo": "new_loan"}
    )

    handler.handle(tx_expansion, mock_seller, mock_buyer, mock_context)
    mock_ledger.record_monetary_expansion.assert_called_once_with(500, source="new_loan", currency="USD")
    mock_ledger.record_monetary_contraction.assert_not_called()
