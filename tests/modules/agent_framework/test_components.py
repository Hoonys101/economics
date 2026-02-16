"""
tests/modules/agent_framework/test_components.py

Unit tests for Agent Framework Components.
Verifies IInventoryComponent and IFinancialComponent implementations.
"""
import pytest
from unittest.mock import MagicMock, ANY

from modules.agent_framework.components.inventory_component import InventoryComponent
from modules.agent_framework.components.financial_component import FinancialComponent
from modules.simulation.api import InventorySlot
from modules.finance.api import DEFAULT_CURRENCY, InsufficientFundsError

class TestInventoryComponent:

    @pytest.fixture
    def inventory(self):
        return InventoryComponent(owner_id="test_agent")

    def test_add_remove_item_main(self, inventory):
        # Add item
        assert inventory.add_item("item_a", 10.0, quality=1.0)
        assert inventory.get_quantity("item_a") == 10.0
        assert inventory.get_quality("item_a") == 1.0

        # Remove partial
        assert inventory.remove_item("item_a", 4.0)
        assert inventory.get_quantity("item_a") == 6.0

        # Remove remainder
        assert inventory.remove_item("item_a", 6.0)
        assert inventory.get_quantity("item_a") == 0.0

    def test_add_remove_item_input(self, inventory):
        # Add item to INPUT slot
        assert inventory.add_item("raw_mat", 50.0, slot=InventorySlot.INPUT, quality=0.8)
        assert inventory.get_quantity("raw_mat", slot=InventorySlot.INPUT) == 50.0
        assert inventory.get_quality("raw_mat", slot=InventorySlot.INPUT) == 0.8

        # Verify isolation from MAIN
        assert inventory.get_quantity("raw_mat", slot=InventorySlot.MAIN) == 0.0

    def test_quality_weighted_average(self, inventory):
        # Add 10 @ 1.0
        inventory.add_item("item_b", 10.0, quality=1.0)
        # Add 10 @ 0.5
        inventory.add_item("item_b", 10.0, quality=0.5)

        # Expected: (10*1.0 + 10*0.5) / 20 = 15/20 = 0.75
        assert inventory.get_quantity("item_b") == 20.0
        assert inventory.get_quality("item_b") == 0.75

    def test_insufficient_remove(self, inventory):
        inventory.add_item("item_c", 5.0)
        assert not inventory.remove_item("item_c", 10.0)
        assert inventory.get_quantity("item_c") == 5.0

    def test_snapshot_restore(self, inventory):
        inventory.add_item("item_d", 10.0, quality=0.9)
        inventory.add_item("item_e", 5.0, slot=InventorySlot.INPUT)

        snapshot = inventory.snapshot()

        new_inventory = InventoryComponent("restored_agent")
        new_inventory.load_from_state(snapshot)

        assert new_inventory.get_quantity("item_d") == 10.0
        assert new_inventory.get_quality("item_d") == 0.9
        assert new_inventory.get_quantity("item_e", slot=InventorySlot.INPUT) == 5.0

    def test_get_inventory_value(self, inventory):
        inventory.add_item("apple", 10.0)
        inventory.add_item("banana", 5.0)

        price_map = {"apple": 100, "banana": 200} # pennies
        # 10*100 + 5*200 = 1000 + 1000 = 2000
        assert inventory.get_inventory_value(price_map) == 2000


class TestFinancialComponent:

    @pytest.fixture
    def finance(self):
        return FinancialComponent(owner_id="101")

    def test_initial_balance(self):
        comp = FinancialComponent("102")
        comp.initialize({"initial_balance": 5000})
        assert comp.balance_pennies == 5000

    def test_deposit_withdraw(self, finance):
        finance.deposit(1000)
        assert finance.balance_pennies == 1000

        finance.withdraw(400)
        assert finance.balance_pennies == 600

    def test_insufficient_funds(self, finance):
        finance.deposit(100)
        with pytest.raises(InsufficientFundsError):
            finance.withdraw(200)
        assert finance.balance_pennies == 100

    def test_credit_frozen(self, finance):
        assert finance.credit_frozen_until_tick == 0
        finance.credit_frozen_until_tick = 100
        assert finance.credit_frozen_until_tick == 100

    def test_net_worth(self, finance):
        finance.deposit(1000)

        # Simple valuation mock
        valuation_func = MagicMock(return_value=500) # 500 pennies assets

        nw = finance.get_net_worth(valuation_func)
        assert nw == 1500
        valuation_func.assert_called_once()

    def test_owner_id_parsing(self):
        # Should handle string ID "123" -> int 123 for Wallet
        f = FinancialComponent("123")
        assert f._wallet.owner_id == 123

        # Should fallback for non-digit
        f2 = FinancialComponent("FIRM_A")
        assert f2._wallet.owner_id == 0
