import unittest
from unittest.mock import Mock, MagicMock
import config
from simulation.firms import Firm
from tests.utils.factories import create_firm_config_dto, create_firm

class TestMarketingROI(unittest.TestCase):
    def setUp(self):
        # Setup common mocks
        self.mock_decision_engine = Mock()
        self.mock_logger = Mock()

        # Configure config module
        self.config_module = config

        # Initialize Firm using Factory
        self.firm = create_firm(
            id=1,
            assets=10000.0,
            initial_liquidity_need=100.0,
            specialization="basic_food",
            productivity_factor=10.0,
            engine=self.mock_decision_engine,
            value_orientation="profit_maximizer",
            config_dto=create_firm_config_dto()
        )
        self.firm.logger = self.mock_logger

        # Reset initial tracking variables for predictable testing
        self.firm.sales_state.marketing_budget_rate = 0.05
        self.firm.finance_state.last_revenue_pennies = 0
        self.firm.finance_state.last_marketing_spend_pennies = 0

        # Mock brand manager
        self.firm.brand_manager = Mock()
        self.firm.sales_state.brand_awareness = 0.5  # Default mid-range
        self.firm.brand_manager.update = Mock()

    def test_budget_increase_on_high_efficiency(self):
        """Test that marketing budget rate increases when ROI is high (> 1.5)."""
        # Step 1: Initial state setup
        # Simulate previous tick: Spend 100.00 (10000 pennies)
        self.firm.sales_state.marketing_budget_pennies = 10000
        self.firm.finance_state.last_marketing_spend_pennies = 10000
        self.firm.finance_state.last_revenue_pennies = 100000 # 1000.00

        # Step 2: Current tick - High Revenue Increase
        # Target Efficiency: delta_revenue / last_spend > 1.5
        # 1.6 = (Current_Rev - 1000) / 100 => Current_Rev - 1000 = 160 => Current_Rev = 1160
        self.firm.finance_state.revenue_this_turn = {"USD": 120000}  # 1200.00. Delta = 200.00, ROI = 2.0

        # Run adjustment
        self.firm._adjust_marketing_budget()

        # Verify
        expected_rate = 0.05 * 1.1  # 0.055
        self.assertAlmostEqual(self.firm.sales_state.marketing_budget_rate, expected_rate)

    def test_budget_decrease_on_low_efficiency(self):
        """Test that marketing budget rate decreases when ROI is low (< 0.8)."""
        # Step 1: Initial state setup
        self.firm.sales_state.marketing_budget_pennies = 10000
        self.firm.finance_state.last_marketing_spend_pennies = 10000
        self.firm.finance_state.last_revenue_pennies = 100000 # 1000.00

        # Step 2: Current tick - Low Revenue Increase
        # Target Efficiency: delta_revenue / last_spend < 0.8
        # 0.5 = (Current_Rev - 1000) / 100 => Current_Rev = 1050
        self.firm.finance_state.revenue_this_turn = {"USD": 105000} # 1050.00. Delta = 50.00, ROI = 0.5

        # Run adjustment
        self.firm._adjust_marketing_budget()

        # Verify
        expected_rate = 0.05 * 0.9  # 0.045
        self.assertAlmostEqual(self.firm.sales_state.marketing_budget_rate, expected_rate)

    def test_budget_stable_on_saturation(self):
        """Test that marketing budget rate remains unchanged when brand awareness is saturated."""
        # Step 1: Initial state setup
        self.firm.sales_state.marketing_budget_pennies = 10000
        self.firm.finance_state.last_marketing_spend_pennies = 10000
        self.firm.finance_state.last_revenue_pennies = 100000 # 1000.00

        # High Efficiency scenario, but saturated
        self.firm.finance_state.revenue_this_turn = {"USD": 150000} # 1500.00. Delta = 500.00, Eff = 5.0 (Very High)
        self.firm.sales_state.brand_awareness = 0.95 # Saturated (> 0.9)

        # Run adjustment
        self.firm._adjust_marketing_budget()

        # Verify
        self.assertEqual(self.firm.sales_state.marketing_budget_rate, 0.05) # Unchanged

    def test_first_tick_skip(self):
        """Test that adjustment is skipped on first tick (no previous spend)."""
        self.firm.finance_state.last_marketing_spend_pennies = 0
        self.firm.sales_state.marketing_budget_pennies = 5000
        self.firm.finance_state.revenue_this_turn = {"USD": 10000}

        self.firm._adjust_marketing_budget()

        # Should update tracking but not rate
        self.assertEqual(self.firm.sales_state.marketing_budget_rate, 0.05)
        self.assertEqual(self.firm.finance_state.last_marketing_spend_pennies, 0) # Not updated here
        # self.assertEqual(self.firm.finance_state.last_revenue, 100.0) # Not updated here

if __name__ == '__main__':
    unittest.main()
