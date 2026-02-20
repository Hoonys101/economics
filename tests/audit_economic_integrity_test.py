
import sys
import unittest
from unittest.mock import MagicMock, PropertyMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List

# Add modules to path
import os
sys.path.insert(0, os.getcwd())
print(f"DEBUG: sys.path: {sys.path}")

# Mock necessary classes/modules
try:
    from modules.system.api import DEFAULT_CURRENCY
except ImportError as e:
    print(f"DEBUG: ImportError details: {e}")
    raise
from simulation.models import Transaction

# Mock EconStateDTO structure
@dataclass
class MockEconState:
    assets: Dict[str, int]
    portfolio: Any
    wallet: Any

# Mock BioStateDTO structure
@dataclass
class MockBioState:
    children_ids: List[int]
    is_active: bool = True

# Mock Household
class MockHousehold:
    def __init__(self, agent_id, assets_pennies):
        self.id = agent_id
        self.name = f"Agent_{agent_id}"

        # Mock wallet
        self.wallet = MagicMock()
        self.wallet.get_balance.return_value = assets_pennies
        self.wallet.get_all_balances.return_value = {DEFAULT_CURRENCY: assets_pennies}

        # Mock Econ State
        self._econ_state = MagicMock()
        self._econ_state.assets = {DEFAULT_CURRENCY: assets_pennies}
        self._econ_state.portfolio.holdings = {}
        self._econ_state.wallet = self.wallet

        # Mock Bio State
        self._bio_state = MockBioState(children_ids=[])

# Mock Government
class MockGovernment:
    def __init__(self, agent_id):
        self.id = agent_id
        self.income_tax_rate = 0.1
        self.record_revenue = MagicMock()

# Mock SimulationState
class MockSimulationState:
    def __init__(self):
        self.time = 100
        self.transaction_processor = MagicMock()
        self.real_estate_units = []
        self.stock_market = MagicMock()
        self.stock_market.get_daily_avg_price.return_value = 10.0 # Float dollars
        self.agents = MagicMock()
        self.bank = MagicMock()
        # Mock debt status
        debt_status = MagicMock()
        debt_status.total_outstanding_debt = 0
        self.bank.get_debt_status.return_value = debt_status

# Import Systems
try:
    from simulation.systems.inheritance_manager import InheritanceManager
    from modules.government.taxation.system import TaxationSystem, TaxIntent
    from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
    from simulation.systems.api import TransactionContext
except ImportError:
    print("Could not import required systems. Ensure you are running from repo root.")
    sys.exit(1)

class TestEconomicIntegrity(unittest.TestCase):

    def setUp(self):
        # Common Config Mock
        self.config_mock = MagicMock()
        self.config_mock.INHERITANCE_DEDUCTION = 10000.0 # Dollars
        self.config_mock.INHERITANCE_TAX_RATE = 0.4
        self.config_mock.SALES_TAX_RATE = 0.05
        self.config_mock.TAX_BRACKETS = []
        self.config_mock.TAX_RATE_BASE = 0.1
        self.config_mock.GOODS_INITIAL_PRICE = {}
        self.config_mock.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        self.config_mock.TAX_MODE = "FLAT" # Simplified
        self.config_mock.INCOME_TAX_PAYER = "HOUSEHOLD"
        self.config_mock.CORPORATE_TAX_RATE = 0.2

    def test_inheritance_integrity(self):
        """Verify InheritanceManager handles pennies correctly (No Inflation)."""
        manager = InheritanceManager(config_module=self.config_mock)

        # Household with 500.00 (50,000 pennies)
        initial_wealth_pennies = 50000
        deceased = MockHousehold(agent_id=1, assets_pennies=initial_wealth_pennies)

        government = MockGovernment(agent_id=999)
        simulation = MockSimulationState()

        # Mock Transaction execution to succeed
        simulation.transaction_processor.execute.return_value = [MagicMock(success=True)]

        # Execute
        transactions = manager.process_death(deceased, government, simulation)

        # Verify Escheatment (No heirs)
        # Expected:
        # Deduction = 10,000 * 100 = 1,000,000 pennies
        # Wealth = 50,000 pennies
        # Taxable = max(0, 50000 - 1000000) = 0
        # Tax = 0
        # Cash left = 50,000
        # Escheat = 50,000

        escheat_tx = next((tx for tx in transactions if tx.transaction_type == "escheatment"), None)
        self.assertIsNotNone(escheat_tx, "Escheatment transaction should be created")

        self.assertEqual(escheat_tx.total_pennies, initial_wealth_pennies,
                         f"INHERITANCE LEAK: Expected {initial_wealth_pennies}, got {escheat_tx.total_pennies}")

    def test_corporate_tax_integrity(self):
        """Verify Corporate Tax calculation uses correct penny values (No Inflation)."""
        # Ensure taxation dict mock returns rate
        self.config_mock.taxation.get.return_value = 0.2

        tax_system = TaxationSystem(config_module=self.config_mock)

        # Mock Firm
        firm = MagicMock()
        firm.is_active = True
        firm.id = 101
        firm.finance = MagicMock()
        # Revenue: 1000.00 (100,000 pennies)
        # Cost: 500.00 (50,000 pennies)
        # Profit: 50,000 pennies
        firm.finance.revenue_this_turn = {DEFAULT_CURRENCY: 100000}
        firm.finance.cost_this_turn = {DEFAULT_CURRENCY: 50000}

        # Execute
        intents = tax_system.generate_corporate_tax_intents([firm], current_tick=10)

        self.assertEqual(len(intents), 1)
        tx = intents[0]

        # Expected Tax: 50,000 * 0.2 = 10,000 pennies
        expected_tax_pennies = 10000

        self.assertEqual(tx.total_pennies, expected_tax_pennies,
                         f"CORPORATE TAX LEAK: Expected {expected_tax_pennies}, got {tx.total_pennies}")

        # Verify Price Display (Should be dollars: 100.00)
        self.assertAlmostEqual(tx.price, 100.0, places=2)

    def test_sales_tax_atomicity(self):
        """Verify Sales Tax is calculated correctly and handled atomically."""
        tax_system = TaxationSystem(config_module=self.config_mock)

        # Mock Transaction (Goods Purchase)
        # Price: $10.00 (1000 pennies)
        # Quantity: 2
        # Total: $20.00 (2000 pennies)
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="widget", quantity=2.0, price=10.0,
            market_id="test", transaction_type="goods", time=10, total_pennies=2000
        )

        buyer = MockHousehold(agent_id=1, assets_pennies=5000) # Has enough
        seller = MagicMock()
        seller.id = 2
        government = MockGovernment(agent_id=999)

        # 1. Verify Tax Calculation
        intents = tax_system.calculate_tax_intents(tx, buyer, seller, government)

        self.assertEqual(len(intents), 1)
        intent = intents[0]

        # Expected Tax: 2000 * 0.05 = 100 pennies ($1.00)
        expected_tax = 100
        self.assertEqual(intent.amount, expected_tax, f"SALES TAX ERROR: Expected {expected_tax}, got {intent.amount}")
        self.assertEqual(intent.payee_id, government.id)

        # 2. Verify Handler Atomicity
        handler = GoodsTransactionHandler()

        # Create Context
        context = MagicMock(spec=TransactionContext)
        context.taxation_system = tax_system
        context.settlement_system = MagicMock()
        context.government = government
        context.market_data = {}
        context.time = 10
        context.config_module = self.config_mock

        # Set settlement to succeed
        context.settlement_system.settle_atomic.return_value = True

        # Execute Handler
        success = handler.handle(tx, buyer, seller, context)

        self.assertTrue(success)

        # Check settle_atomic calls
        # Expected Credits:
        # Seller: 2000
        # Gov: 100
        context.settlement_system.settle_atomic.assert_called_once()
        args = context.settlement_system.settle_atomic.call_args
        debit_agent, credits_list, tick = args[0]

        self.assertEqual(debit_agent, buyer)
        self.assertEqual(len(credits_list), 2)

        # Verify credits content
        seller_credit = next((amt for ag, amt, memo in credits_list if ag.id == seller.id), None)
        gov_credit = next((amt for ag, amt, memo in credits_list if ag.id == government.id), None)

        self.assertEqual(seller_credit, 2000, "Seller should get full trade value")
        self.assertEqual(gov_credit, 100, "Government should get tax amount")

if __name__ == '__main__':
    unittest.main()
