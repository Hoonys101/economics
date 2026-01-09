import unittest
from unittest.mock import MagicMock
from simulation.models import RealEstateUnit, Transaction, Order, Loan
from simulation.bank import Bank
from simulation.decisions.housing_manager import HousingManager
from simulation.engine import Simulation
from simulation.core_agents import Household
from simulation.markets.order_book_market import OrderBookMarket

class TestRealEstateSales(unittest.TestCase):
    def setUp(self):
        # Mock Config
        self.config = MagicMock()
        # Set float/int values explicitly to avoid MagicMock format/compare errors
        self.config.INITIAL_PROPERTY_VALUE = 10000.0
        self.config.INITIAL_RENT_PRICE = 100.0
        self.config.INITIAL_BANK_ASSETS = 1000000.0
        self.config.INITIAL_BASE_ANNUAL_RATE = 0.05
        self.config.CB_INFLATION_TARGET = 0.02
        self.config.CB_UPDATE_INTERVAL = 10
        self.config.CB_TAYLOR_ALPHA = 0.5
        self.config.CB_TAYLOR_BETA = 0.5
        self.config.NUM_HOUSING_UNITS = 10
        self.config.GOODS = {"consumer_goods": {}}
        self.config.BATCH_SAVE_INTERVAL = 10
        self.config.MAINTENANCE_RATE_PER_TICK = 0.001
        self.config.HOMELESS_PENALTY_PER_TICK = 50.0
        self.config.SALES_TAX_RATE = 0.0
        self.config.INCOME_TAX_RATE = 0.0
        self.config.MORTGAGE_SPREAD = 0.01
        self.config.CREDIT_SPREAD_BASE = 0.02
        self.config.BANK_MARGIN = 0.02
        self.config.TICKS_PER_YEAR = 100
        self.config.LOAN_DEFAULT_TERM = 50
        self.config.MORTGAGE_DEFAULT_THRESHOLD = 3
        self.config.TARGET_POPULATION = 100 # For mitosis check in init

        # Setup Simulation Components (Minimal)
        self.bank = Bank(id=999, initial_assets=1000000.0, config_module=self.config)
        self.housing_market = OrderBookMarket("real_estate")

        # Agents
        self.buyer = MagicMock(spec=Household)
        self.buyer.id = 1
        self.buyer.assets = 3000.0
        self.buyer.owned_properties = []
        self.buyer.residing_property_id = None
        self.buyer.is_active = True
        # Engine tries to set decision_engine.markets on init
        self.buyer.decision_engine = MagicMock()
        self.buyer.needs = {"survival": 0.0}
        self.buyer.inventory = {"food": 0.0}

        self.seller = MagicMock()
        self.seller.id = 0
        self.seller.assets = 0.0
        self.seller.is_active = True

        # Unit
        self.unit = RealEstateUnit(id=5, estimated_value=10000.0, owner_id=0)

    def test_mortgage_creation_and_transaction(self):
        """Test atomic mortgage creation during transaction processing."""
        tx = Transaction(
            buyer_id=1,
            seller_id=0,
            item_id="unit_5",
            quantity=1.0,
            price=10000.0,
            market_id="real_estate",
            transaction_type="housing",
            time=1
        )

        sim_real = Simulation(
            households=[self.buyer],
            firms=[],
            ai_trainer=MagicMock(),
            repository=MagicMock(),
            config_module=self.config,
            goods_data=[],
            logger=MagicMock()
        )
        sim_real.bank = self.bank
        sim_real.agents = {1: self.buyer, 0: self.seller, 999: self.bank}
        sim_real.real_estate_units = [self.unit]
        sim_real.markets["real_estate"] = self.housing_market

        sim_real._process_transactions([tx])

        self.assertEqual(self.unit.owner_id, 1)
        self.assertEqual(self.unit.occupant_id, 1)
        self.assertAlmostEqual(self.buyer.assets, 1000.0)
        self.assertAlmostEqual(self.seller.assets, 10000.0)
        self.assertAlmostEqual(self.bank.assets, 1000000.0 - 8000.0)

        self.assertIsNotNone(self.unit.mortgage_id)
        loan = self.bank.loans[self.unit.mortgage_id]
        self.assertEqual(loan.principal, 8000.0)
        self.assertEqual(loan.borrower_id, 1)
        self.assertEqual(loan.collateral_id, 5)

    def test_housing_manager_logic(self):
        """Test NPV logic."""
        buy = HousingManager.should_buy(
            household=self.buyer,
            unit_price=50000.0,
            rent_price=10.0,
            interest_rate=0.05,
            appreciation_rate=0.0
        )
        self.assertFalse(buy, "Should NOT buy when rent is extremely cheap and no appreciation")

        buy = HousingManager.should_buy(
            household=self.buyer,
            unit_price=10000.0,
            rent_price=500.0,
            interest_rate=0.01,
            appreciation_rate=0.002
        )
        self.assertTrue(buy, "Should BUY when rent is expensive")

    def test_foreclosure(self):
        """Test foreclosure flow."""
        loan_id = self.bank.grant_mortgage(borrower_id=1, property_id=5, principal=8000.0)
        self.unit.mortgage_id = loan_id
        self.unit.owner_id = 1

        self.bank.mortgage_default_counter[loan_id] = 3

        defaults = self.bank.check_mortgage_defaults()
        self.assertIn(loan_id, defaults)

        success = self.bank.foreclose_property(loan_id, [self.unit], self.housing_market)
        self.assertTrue(success)

        self.assertEqual(self.unit.owner_id, self.bank.id)
        self.assertIsNone(self.unit.occupant_id)
        self.assertIsNone(self.unit.mortgage_id)

        self.assertEqual(len(self.housing_market.sell_orders["unit_5"]), 1)
        order = self.housing_market.sell_orders["unit_5"][0]
        self.assertEqual(order.price, 8000.0)

if __name__ == '__main__':
    unittest.main()
