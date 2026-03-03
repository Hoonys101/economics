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


