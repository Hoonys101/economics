import unittest
from unittest.mock import MagicMock
from modules.housing.api import (
    HouseholdHousingStateDTO,
    HousingMarketStateDTO,
    RealEstateUnitDTO,
    HousingActionType,
    HousingDecisionDTO
)
from modules.housing.planner import HousingPlanner

class TestHousingPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = HousingPlanner()
        self.config = MagicMock()

        # Setup default config mock
        self.config.housing.RENT_TO_INCOME_RATIO_MAX = 0.3
        self.config.housing.FINANCIAL_DISTRESS_ASSET_THRESHOLD_MONTHS = 3.0
        self.config.housing.MORTGAGE_TO_INCOME_RATIO_MAX = 0.4

        self.config.finance.MORTGAGE_DOWN_PAYMENT_RATE = 0.2
        self.config.finance.MORTGAGE_INTEREST_RATE = 0.05 # 5%
        self.config.finance.MORTGAGE_TERM_YEARS = 30

    def test_priority1_homelessness_finds_rental(self):
        # Household: Homeless, income 5000/mo
        household = HouseholdHousingStateDTO(
            id=1, assets=10000, income=5000, is_homeless=True,
            residing_property_id=None, owned_property_ids=[], needs={}
        )

        # Max rent = 5000 * 0.3 = 1500

        # Market: One expensive unit, one affordable unit
        unit_expensive = RealEstateUnitDTO(
            id=101, owner_id=99, estimated_value=200000, rent_price=2000, for_sale_price=200000,
            on_market_for_rent=True, on_market_for_sale=False
        )
        unit_cheap = RealEstateUnitDTO(
            id=102, owner_id=99, estimated_value=100000, rent_price=1000, for_sale_price=100000,
            on_market_for_rent=True, on_market_for_sale=False
        )

        market = HousingMarketStateDTO(units_for_sale=[], units_for_rent=[unit_expensive, unit_cheap])

        decision = self.planner.evaluate_and_decide(household, market, self.config)

        self.assertEqual(decision.action, HousingActionType.SEEK_RENTAL)
        self.assertEqual(decision.target_unit_id, 102)

    def test_priority1_homelessness_cannot_afford_rental(self):
        # Household: Homeless, low income
        household = HouseholdHousingStateDTO(
            id=1, assets=0, income=1000, is_homeless=True,
            residing_property_id=None, owned_property_ids=[], needs={}
        )
        # Max rent = 300

        unit = RealEstateUnitDTO(
            id=101, owner_id=99, estimated_value=100000, rent_price=500, for_sale_price=100000,
            on_market_for_rent=True, on_market_for_sale=False
        )

        market = HousingMarketStateDTO(units_for_sale=[], units_for_rent=[unit])

        decision = self.planner.evaluate_and_decide(household, market, self.config)

        self.assertEqual(decision.action, HousingActionType.STAY)
        self.assertEqual(decision.justification, "Agent is homeless but cannot afford any available rentals.")

    def test_priority2_financial_distress_sells_property(self):
        # Household: Owns property 202, low assets relative to income threshold
        # Threshold = income * 3.0
        income = 5000
        threshold = 15000

        household = HouseholdHousingStateDTO(
            id=1, assets=5000, income=income, is_homeless=False,
            residing_property_id=202, owned_property_ids=[202], needs={}
        )

        market = HousingMarketStateDTO(units_for_sale=[], units_for_rent=[])

        decision = self.planner.evaluate_and_decide(household, market, self.config)

        self.assertEqual(decision.action, HousingActionType.SELL_PROPERTY)
        self.assertEqual(decision.sell_unit_id, 202)
        self.assertIn("financial distress", decision.justification)

    def test_priority3_upgrade_renter_buys_home(self):
        # Household: Renter (residing != owned), rich enough
        # Income 10000, Assets 100,000
        household = HouseholdHousingStateDTO(
            id=1, assets=100000, income=10000, is_homeless=False,
            residing_property_id=101, owned_property_ids=[], needs={}
        )

        # House for sale: 300,000
        # Down payment (20%): 60,000 (Affordable, assets > 60k)
        # Loan: 240,000
        # Monthly payment approx: (240000 * 0.05 / 12) ~ 1000 (very rough estimate, assuming simple interest logic check)
        # Mortgage limit: 10000 * 0.4 = 4000

        unit_sale = RealEstateUnitDTO(
            id=303, owner_id=99, estimated_value=300000, rent_price=0, for_sale_price=300000,
            on_market_for_rent=False, on_market_for_sale=True
        )

        market = HousingMarketStateDTO(units_for_sale=[unit_sale], units_for_rent=[])

        decision = self.planner.evaluate_and_decide(household, market, self.config)

        self.assertEqual(decision.action, HousingActionType.SEEK_PURCHASE)
        self.assertEqual(decision.target_unit_id, 303)

    def test_priority3_upgrade_renter_cannot_afford_down_payment(self):
        # Household: Renter, decent income but low assets
        household = HouseholdHousingStateDTO(
            id=1, assets=10000, income=10000, is_homeless=False,
            residing_property_id=101, owned_property_ids=[], needs={}
        )

        # House 300,000 -> Down payment 60,000
        unit_sale = RealEstateUnitDTO(
            id=303, owner_id=99, estimated_value=300000, rent_price=0, for_sale_price=300000,
            on_market_for_rent=False, on_market_for_sale=True
        )

        market = HousingMarketStateDTO(units_for_sale=[unit_sale], units_for_rent=[])

        decision = self.planner.evaluate_and_decide(household, market, self.config)

        self.assertEqual(decision.action, HousingActionType.STAY)

    def test_default_stay(self):
        # Household: Renter, comfortable, no houses for sale, no distress
        household = HouseholdHousingStateDTO(
            id=1, assets=50000, income=5000, is_homeless=False,
            residing_property_id=101, owned_property_ids=[], needs={}
        )

        market = HousingMarketStateDTO(units_for_sale=[], units_for_rent=[])

        decision = self.planner.evaluate_and_decide(household, market, self.config)

        self.assertEqual(decision.action, HousingActionType.STAY)
