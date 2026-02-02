import unittest
from unittest.mock import Mock, MagicMock
import config
from simulation.firms import Firm
from tests.utils.factories import create_firm_config_dto

class TestMarketingROI(unittest.TestCase):
    def setUp(self):
        # Setup common mocks
        self.mock_decision_engine = Mock()
        self.mock_logger = Mock()

        # Configure config module
        self.config_module = config

        # Initialize Firm
        self.firm = Firm(
            id=1,
            initial_capital=10000.0,
            initial_liquidity_need=100.0,
            specialization="basic_food",
            productivity_factor=10.0,
            decision_engine=self.mock_decision_engine,
            value_orientation="profit_maximizer",
            config_dto=create_firm_config_dto(),
            logger=self.mock_logger
        )

        # Reset initial tracking variables for predictable testing
        self.firm.marketing_budget_rate = 0.05
        self.firm.last_revenue = 0.0
        self.firm.last_marketing_spend = 0.0

        # Mock brand manager
        self.firm.brand_manager = Mock()
        self.firm.brand_manager.brand_awareness = 0.5  # Default mid-range
        self.firm.brand_manager.update = Mock()

    @unittest.skip("Legacy Mutation Assertion: Needs migration to Order Verification")
    def test_budget_increase_on_high_efficiency(self):
        """Test that marketing budget rate increases when ROI is high (> 1.5)."""
        # Step 1: Initial state setup
        # Simulate previous tick: Spend 100
        self.firm.marketing_budget = 100.0
        self.firm.last_marketing_spend = 100.0
        self.firm.last_revenue = 1000.0

        # Step 2: Current tick - High Revenue Increase
        # Target Efficiency: delta_revenue / last_spend > 1.5
        # 1.6 = (Current_Rev - 1000) / 100 => Current_Rev - 1000 = 160 => Current_Rev = 1160
        self.firm.finance.revenue_this_turn = 1200.0  # Delta = 200, Eff = 2.0

        # Run adjustment
        self.firm._adjust_marketing_budget()

        # Verify
        expected_rate = 0.05 * 1.1  # 0.055
        self.assertAlmostEqual(self.firm.marketing_budget_rate, expected_rate)
        self.assertEqual(self.firm.last_revenue, 1200.0)

    @unittest.skip("Legacy Mutation Assertion: Needs migration to Order Verification")
    def test_budget_decrease_on_low_efficiency(self):
        """Test that marketing budget rate decreases when ROI is low (< 0.8)."""
        # Step 1: Initial state setup
        self.firm.marketing_budget = 100.0
        self.firm.last_marketing_spend = 100.0
        self.firm.last_revenue = 1000.0

        # Step 2: Current tick - Low Revenue Increase
        # Target Efficiency: delta_revenue / last_spend < 0.8
        # 0.5 = (Current_Rev - 1000) / 100 => Current_Rev = 1050
        self.firm.finance.revenue_this_turn = 1050.0 # Delta = 50, Eff = 0.5

        # Run adjustment
        self.firm._adjust_marketing_budget()

        # Verify
        expected_rate = 0.05 * 0.9  # 0.045
        self.assertAlmostEqual(self.firm.marketing_budget_rate, expected_rate)

    def test_budget_stable_on_saturation(self):
        """Test that marketing budget rate remains unchanged when brand awareness is saturated."""
        # Step 1: Initial state setup
        self.firm.marketing_budget = 100.0
        self.firm.last_marketing_spend = 100.0
        self.firm.last_revenue = 1000.0

        # High Efficiency scenario, but saturated
        self.firm.finance.revenue_this_turn = 1500.0 # Delta = 500, Eff = 5.0 (Very High)
        self.firm.brand_manager.brand_awareness = 0.95 # Saturated (> 0.9)

        # Run adjustment
        self.firm._adjust_marketing_budget()

        # Verify
        self.assertEqual(self.firm.marketing_budget_rate, 0.05) # Unchanged

    @unittest.skip("Legacy Mutation Assertion: Needs migration to Order Verification")
    def test_first_tick_skip(self):
        """Test that adjustment is skipped on first tick (no previous spend)."""
        self.firm.last_marketing_spend = 0.0
        self.firm.marketing_budget = 50.0
        self.firm.finance.revenue_this_turn = 100.0

        self.firm._adjust_marketing_budget()

        # Should update tracking but not rate
        self.assertEqual(self.firm.marketing_budget_rate, 0.05)
        self.assertEqual(self.firm.last_marketing_spend, 50.0)
        self.assertEqual(self.firm.last_revenue, 100.0)

if __name__ == '__main__':
    unittest.main()
