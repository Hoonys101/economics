
import unittest
from unittest.mock import MagicMock, PropertyMock
from typing import Any, Dict

from modules.government.taxation.system import TaxationSystem, TaxIntent
from simulation.models import Transaction
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.handlers.inheritance_handler import InheritanceHandler
from simulation.systems.handlers.emergency_handler import EmergencyTransactionHandler
from simulation.systems.api import TransactionContext
from modules.finance.wallet.wallet import Wallet
from modules.system.api import DEFAULT_CURRENCY

class MockAgent:
    def __init__(self, agent_id, assets=0):
        self.id = agent_id
        self.wallet = Wallet(agent_id, {DEFAULT_CURRENCY: assets})
        self.assets = assets # Legacy property (float/int confusion)
        self._econ_state = MagicMock()
        self._econ_state.assets = assets
        self._econ_state.portfolio.holdings = {}
        self._bio_state = MagicMock()
        self._bio_state.children_ids = []
        self._bio_state.is_active = True

    def get_balance(self, currency):
        return self.wallet.get_balance(currency)

    def deposit(self, amount, currency=DEFAULT_CURRENCY):
        self.wallet.add(amount, currency)
        self.assets = self.wallet.get_balance(currency)
        self._econ_state.assets = self.assets

    def withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self.wallet.subtract(amount, currency)
        self.assets = self.wallet.get_balance(currency)
        self._econ_state.assets = self.assets

    def record_revenue(self, *args, **kwargs):
        pass

class MockConfig:
    SALES_TAX_RATE = 0.10 # 10%
    INHERITANCE_TAX_RATE = 0.50 # 50%
    INHERITANCE_DEDUCTION = 1000.0 # 1000 pennies ($10)
    DEFAULT_BASIC_FOOD_PRICE = 500

class TestEconomicIntegrity(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        self.tax_system = TaxationSystem(self.config)
        self.gov = MockAgent(999, 0) # Government
        self.buyer = MockAgent(1, 10000)
        self.seller = MockAgent(2, 5000)

        # Mock Settlement System
        self.settlement_system = MagicMock()
        self.settlement_system.settle_atomic.return_value = True

        # Mock TransactionContext
        self.context = TransactionContext(
            agents={1: self.buyer, 2: self.seller, 999: self.gov},
            inactive_agents={},
            government=self.gov,
            settlement_system=self.settlement_system,
            taxation_system=self.tax_system,
            stock_market=None,
            real_estate_units=[],
            market_data={},
            config_module=self.config,
            logger=MagicMock(),
            time=1,
            bank=None,
            central_bank=None,
            public_manager=None,
            transaction_queue=[],
            shareholder_registry=None
        )

    def test_sales_tax_atomicity_emergency_buy(self):
        """Verify that emergency_buy triggers sales tax."""
        tx = Transaction(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            item_id="basic_food",
            quantity=10.0,
            price=100, # 100 pennies per unit
            market_id="system",
            transaction_type="emergency_buy",
            time=1
        )

        # 1. Check TaxationSystem calculation directly
        intents = self.tax_system.calculate_tax_intents(
            tx, self.buyer, self.seller, self.gov
        )

        # Expectation: 10 * 100 = 1000 trade value. Tax 10% = 100.
        # CURRENTLY FAILS: calculate_tax_intents ignores emergency_buy
        has_tax = any(i.amount == 100 for i in intents)
        if not has_tax:
            print("\n[FAIL] Sales Tax missing for emergency_buy!")
        else:
            print("\n[PASS] Sales Tax present for emergency_buy.")

        # 2. Check EmergencyHandler integration
        handler = EmergencyTransactionHandler()
        handler.handle(tx, self.buyer, self.seller, self.context)

        # Verify settlement arguments
        # credits should contain: (seller, 1000), (gov, 100)
        call_args = self.settlement_system.settle_atomic.call_args
        if call_args:
            buyer_arg, credits_arg, time_arg = call_args[0]
            gov_credit = next((c for c in credits_arg if c[0].id == 999), None)

            if not gov_credit:
                 print("[FAIL] Settlement Atomic does not include Government credit!")
            elif gov_credit[1] != 100:
                 print(f"[FAIL] Government credit incorrect: {gov_credit[1]} != 100")
            else:
                 print("[PASS] Settlement Atomic includes correct tax.")
        else:
            print("[FAIL] settle_atomic not called!")

    def test_inheritance_integrity(self):
        """Verify InheritanceManager uses integer math and doesn't drift."""
        deceased = MockAgent(10, 10005) # 10005 pennies (100.05 dollars)
        heir = MockAgent(11, 0)

        # Setup InheritanceManager
        manager = InheritanceManager(self.config)

        # Mock SimulationState
        sim_state = MagicMock()
        sim_state.time = 1
        sim_state.real_estate_units = []
        sim_state.stock_market = None
        sim_state.settlement_system = self.settlement_system
        sim_state.agents = {10: deceased, 11: heir, 999: self.gov}
        # TransactionProcessor mock
        sim_state.transaction_processor = MagicMock()

        # We need to mock execute to simulate wallet updates if liquidation happens
        # But for this test, let's focus on the initial calculation and tax transaction

        deceased._bio_state.children_ids = [11]

        # Run process_death
        transactions = manager.process_death(deceased, self.gov, sim_state)

        # Check Tax Transaction
        # Wealth = 10005. Deduction = 1000. Taxable = 9005. Tax (50%) = 4502.5 -> Round?
        # If float math: 10005 pennies -> 100.05 dollars (assets property)
        # If manager uses float assets: cash = 100.05
        # Deduction = 1000.0 (dollars? or pennies?). Config says 1000.0.
        # If Deduction is 1000.0 dollars: Taxable = 0. Tax = 0.
        # If Deduction is 1000.0 pennies (10 dollars): Taxable = 90.05. Tax = 45.025 -> 45.03 dollars? -> 4503 pennies?

        # Wait, manager does:
        # cash_raw = deceased._econ_state.assets (10005)
        # cash = round(cash, 2) -> 10005 (It treats it as float but value is integer magnitude)
        # tax_amount = round((10005 - 1000) * 0.5, 2) = round(9005 * 0.5, 2) = 4502.50

        # If using float math, 4502.5 might be 4502.5
        # But transaction price must be what?
        # If passed to transaction as float, it's fine.

        # But if we distribute:
        # Tax = 4502.5
        # Remaining = 10005 - 4502.5 = 5502.5

        # Transaction price for distribution will be 5502.5

        # BUT InheritanceHandler uses `deceased.wallet.get_balance()` which is 10005 (int).
        # It ignores the price in the transaction.
        # So handler distributes 10005 (minus tax if tax was executed separately).

        # InheritanceManager executes tax transaction first:
        # tx price = 4502.5.
        # If TransactionProcessor executes this, it might fail or truncate if it expects int.
        # Or if it processes 4502.5, the wallet becomes 10005 - 4502.5 = 5502.5 (float).

        # Then Distribution Transaction:
        # price = 5502.5.
        # Handler sees wallet 5502.5. Distributes 5502.5.

        # The drift comes if `round` behaves differently or if we lose pennies.
        # e.g. 1/3 split.

        print(f"\n[INFO] Initial Assets: {deceased.assets}")
        for tx in transactions:
            print(f"[TX] Type: {tx.transaction_type}, Price: {tx.price}, Item: {tx.item_id}")
            if tx.transaction_type == "tax":
                print(f"[CHECK] Tax Amount: {tx.price}")
            if tx.transaction_type == "inheritance_distribution":
                print(f"[CHECK] Dist Amount: {tx.price}")

if __name__ == '__main__':
    unittest.main()
