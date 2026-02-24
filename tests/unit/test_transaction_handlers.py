import unittest
from unittest.mock import MagicMock, ANY
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.systems.handlers.labor_handler import LaborTransactionHandler
from modules.finance.api import IFinancialAgent
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from simulation.agents.government import Government
from modules.government.taxation.system import TaxationSystem

class TestGoodsTransactionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = GoodsTransactionHandler()
        self.settlement = MagicMock()

        # Mock Government
        self.government = MagicMock(spec=Government)
        self.government.id = 99

        self.escrow_agent = MagicMock()
        self.config = MagicMock()
        self.logger = MagicMock()
        self.taxation_system = MagicMock(spec=TaxationSystem)

        # Use simple MagicMock for state to avoid spec issues
        self.state = MagicMock()
        self.state.settlement_system = self.settlement
        self.state.government = self.government
        self.state.escrow_agent = self.escrow_agent
        self.state.config_module = self.config
        self.state.logger = self.logger
        self.state.time = 100
        self.state.market_data = {}
        self.state.taxation_system = self.taxation_system
        self.state.transaction_queue = []

        # Mock Buyer with IFinancialAgent protocol
        self.buyer = MagicMock(spec=IFinancialAgent)
        self.buyer.id = 1
        self.buyer.assets = 10000
        self.buyer.get_balance.return_value = 10000

        self.seller = MagicMock()
        self.seller.id = 2

        # Setup config
        self.config.SALES_TAX_RATE = 0.10

    def test_goods_success_atomic(self):
        # Transaction: 10 units @ 100 pennies = 1000 pennies
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=100,
            transaction_type="goods", time=100, market_id="goods_market",
            total_pennies=1000
        )

        # Mock Tax Intents
        intent_mock = MagicMock()
        intent_mock.amount = 100
        intent_mock.reason = "sales_tax:apple"
        intent_mock.payer_id = 1
        intent_mock.payee_id = 99

        self.taxation_system.calculate_tax_intents.return_value = [intent_mock]

        # Settle Atomic Success
        self.settlement.settle_atomic.return_value = True

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        # Verify settle_atomic called
        # Credits: [(seller, 1000, "goods_trade:apple"), (government, 100, "sales_tax:apple")]
        call_args = self.settlement.settle_atomic.call_args
        self.assertIsNotNone(call_args)
        args, kwargs = call_args

        # Check debit agent is buyer
        self.assertEqual(args[0], self.buyer)

        # Check credits
        credits = args[1]
        self.assertEqual(len(credits), 2)

        # Check seller credit
        self.assertIn((self.seller, 1000, "goods_trade:apple"), credits)
        # Check gov credit
        self.assertIn((self.government, 100, "sales_tax:apple"), credits)

        # Verify Gov Record Revenue
        self.government.record_revenue.assert_called()

        # WO-IMPL-LEDGER-HARDENING: Verify Tax Transaction Generation
        self.assertEqual(len(self.state.transaction_queue), 1)
        tax_tx = self.state.transaction_queue[0]
        self.assertEqual(tax_tx.transaction_type, "tax")
        self.assertEqual(tax_tx.total_pennies, 100)
        self.assertEqual(tax_tx.metadata["executed"], True)

    def test_goods_settle_fail(self):
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=100,
            transaction_type="goods", time=100, market_id="goods_market",
            total_pennies=1000
        )

        self.taxation_system.calculate_tax_intents.return_value = []
        self.settlement.settle_atomic.return_value = False

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)

class TestLaborTransactionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = LaborTransactionHandler()
        self.settlement = MagicMock()

        self.government = MagicMock(spec=Government)
        self.government.id = 99

        self.config = MagicMock()
        self.logger = MagicMock()
        self.taxation_system = MagicMock(spec=TaxationSystem)

        self.state = MagicMock()
        self.state.settlement_system = self.settlement
        self.state.government = self.government
        self.state.config_module = self.config
        self.state.logger = self.logger
        self.state.time = 100
        self.state.market_data = {}
        self.state.taxation_system = self.taxation_system

        self.buyer = MagicMock()
        self.buyer.id = 1
        self.seller = MagicMock()
        self.seller.id = 2

        self.config.INCOME_TAX_PAYER = "HOUSEHOLD"
        self.config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        self.config.GOODS_INITIAL_PRICE = {"basic_food": 500}

    def test_labor_atomic_settlement(self):
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="labor", quantity=1, price=2000,
            transaction_type="labor", time=100, market_id="labor_market",
            total_pennies=2000
        )

        # Mock Tax Intents: Seller pays tax
        intent_mock = MagicMock()
        intent_mock.amount = 200
        intent_mock.reason = "income_tax_household"
        intent_mock.payer_id = 2 # Seller
        intent_mock.payee_id = 99 # Gov

        self.taxation_system.calculate_tax_intents.return_value = [intent_mock]
        self.settlement.settle_atomic.return_value = True

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        # Verify Atomic Settlement
        # Seller Net = 2000 - 200 = 1800
        # Credits: [(Gov, 200, "income_tax_household"), (Seller, 1800, "labor_wage:labor")]

        call_args = self.settlement.settle_atomic.call_args
        self.assertIsNotNone(call_args)
        args, kwargs = call_args

        self.assertEqual(args[0], self.buyer)
        credits = args[1]
        self.assertEqual(len(credits), 2)

        # Check credits content
        self.assertIn((self.government, 200, "income_tax_household"), credits)
        self.assertIn((self.seller, 1800, "labor_wage:labor"), credits)

        self.government.record_revenue.assert_called()
