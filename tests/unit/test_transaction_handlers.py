import unittest
from unittest.mock import MagicMock, ANY
from modules.finance.transaction.handlers.goods import GoodsTransactionHandler
from modules.finance.transaction.handlers.labor import LaborTransactionHandler
from modules.finance.transaction.handlers.protocols import ISolvent, ITaxCollector
from simulation.models import Transaction
from simulation.dtos.api import SimulationState

class TestGoodsTransactionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = GoodsTransactionHandler()
        self.settlement = MagicMock()

        # Mock Government with ITaxCollector protocol
        self.government = MagicMock(spec=ITaxCollector)
        self.government.id = 99

        self.escrow_agent = MagicMock()
        self.config = MagicMock()
        self.logger = MagicMock()
        self.state = MagicMock(spec=SimulationState)
        self.state.settlement_system = self.settlement
        self.state.government = self.government
        self.state.escrow_agent = self.escrow_agent
        self.state.config_module = self.config
        self.state.logger = self.logger
        self.state.time = 100
        self.state.market_data = {}

        # Mock Buyer with ISolvent protocol
        self.buyer = MagicMock(spec=ISolvent)
        self.buyer.id = 1
        # Set assets to sufficient amount by default to avoid issues
        self.buyer.assets = 10000

        self.seller = MagicMock()
        self.seller.id = 2

        # Setup config
        self.config.SALES_TAX_RATE = 0.10 # 10% for easy math

    def test_goods_success(self):
        # Transaction: 10 units @ 100 pennies = 1000 pennies
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=100,
            transaction_type="goods", time=100, market_id="goods_market",
            total_pennies=1000
        )

        # Expectation:
        # Trade Value = 1000
        # Tax = 1000 * 0.10 = 100
        # Total Cost = 1100

        self.settlement.transfer.return_value = True
        self.settlement.settle_atomic.return_value = True

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        # Verify Escrow Transfer (Buyer -> Escrow)
        self.settlement.transfer.assert_called_with(self.buyer, self.escrow_agent, 1100, "escrow_hold:apple", tick=100)

        # Verify Atomic Settlement
        expected_credits = [
            (self.seller, 1000, "goods_trade:apple"),
            (self.government, 100, "sales_tax:apple")
        ]
        self.settlement.settle_atomic.assert_called_with(
            debit_agent=self.escrow_agent,
            credits_list=expected_credits,
            tick=100
        )

        # Verify Gov Record Revenue
        self.government.record_revenue.assert_called_once()

    def test_goods_escrow_fail(self):
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=100,
            transaction_type="goods", time=100, market_id="goods_market",
            total_pennies=1000
        )

        # Escrow transfer fails
        self.settlement.transfer.side_effect = [False]

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)
        # Should stop after first transfer attempt
        self.assertEqual(self.settlement.transfer.call_count, 1)

    def test_goods_trade_fail_rollback(self):
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="apple", quantity=10, price=100,
            transaction_type="goods", time=100, market_id="goods_market",
            total_pennies=1000
        )

        # 1. Escrow (Success), 2. Atomic (Fail), 3. Rollback (Success)
        self.settlement.transfer.side_effect = [True, True] # Escrow success, Rollback success
        self.settlement.settle_atomic.return_value = False

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)

        # Verify calls
        # 1. Buyer -> Escrow (1100)
        self.settlement.transfer.assert_any_call(self.buyer, self.escrow_agent, 1100, "escrow_hold:apple", tick=100)

        # 2. Atomic Settlement (Fail)
        self.settlement.settle_atomic.assert_called()

        # 3. Escrow -> Buyer (1100) (ROLLBACK)
        self.settlement.transfer.assert_any_call(self.escrow_agent, self.buyer, 1100, "escrow_reversal:distribution_failure", tick=100)

class TestLaborTransactionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = LaborTransactionHandler()
        self.settlement = MagicMock()

        # Mock Government with ITaxCollector protocol
        self.government = MagicMock(spec=ITaxCollector)

        self.config = MagicMock()
        self.logger = MagicMock()
        self.state = MagicMock(spec=SimulationState)
        self.state.settlement_system = self.settlement
        self.state.government = self.government
        self.state.config_module = self.config
        self.state.logger = self.logger
        self.state.time = 100
        self.state.market_data = {}

        self.buyer = MagicMock()
        self.buyer.id = 1
        self.seller = MagicMock()
        self.seller.id = 2

        # Defaults
        self.config.INCOME_TAX_PAYER = "HOUSEHOLD"
        self.config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        self.config.GOODS_INITIAL_PRICE = {"basic_food": 500} # 500 pennies

    def test_labor_household_tax_payer(self):
        # Transaction: 1 unit labor @ 2000 pennies
        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="labor", quantity=1, price=2000,
            transaction_type="labor", time=100, market_id="labor_market",
            total_pennies=2000
        )

        # Mock Gov tax calc
        self.government.calculate_income_tax.return_value = 200 # 10%
        self.settlement.transfer.return_value = True

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        # Verify Wage Transfer (Buyer -> Seller) Gross
        self.settlement.transfer.assert_called_with(self.buyer, self.seller, 2000, "labor_wage_gross:labor")

        # Verify Tax Collection (Gov collects from Seller/Household)
        self.government.collect_tax.assert_called_with(200, "income_tax_household", self.seller, 100)

    def test_labor_firm_tax_payer(self):
        self.config.INCOME_TAX_PAYER = "FIRM"

        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="labor", quantity=1, price=2000,
            transaction_type="labor", time=100, market_id="labor_market",
            total_pennies=2000
        )

        self.government.calculate_income_tax.return_value = 200
        self.settlement.transfer.return_value = True

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        # Verify Wage Transfer (Buyer -> Seller) Net? No, code says "trade_value" (Gross)
        # "Firm pays Wage to Household"
        self.settlement.transfer.assert_called_with(self.buyer, self.seller, 2000, "labor_wage:labor")

        # Verify Tax Collection (Gov collects from Buyer/Firm)
        self.government.collect_tax.assert_called_with(200, "income_tax_firm", self.buyer, 100)
