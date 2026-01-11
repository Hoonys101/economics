
import unittest
from unittest.mock import Mock, MagicMock
from simulation.decisions.corporate_manager import CorporateManager

class TestAutomationTax(unittest.TestCase):
    def setUp(self):
        self.mock_config = Mock()
        # Constants from config
        self.mock_config.AUTOMATION_COST_PER_PCT = 1000.0
        self.mock_config.FIRM_SAFETY_MARGIN = 2000.0
        self.mock_config.AUTOMATION_TAX_RATE = 0.05

        self.manager = CorporateManager(self.mock_config)
        self.mock_firm = Mock()
        self.mock_firm.id = 1
        self.mock_firm.automation_level = 0.5
        self.mock_firm.assets = 10000.0
        self.mock_firm.revenue_this_turn = 5000.0

        # Setup guidance mock
        self.mock_guidance = {"target_automation": 0.6} # Target 0.6 (Gap 0.1)

        self.mock_government = Mock()

    def test_automation_tax_applied(self):
        # Setup: Ensure firm has enough budget
        # Investable = 10000 - 2000 = 8000
        # Target Gap = 0.1 (10%). Cost per pct = 1000.
        # Cost = 1000 * 10 = 10,000.
        # Budget = 8000 * (aggressiveness * 0.5) = 4000.
        # Actual spend = min(10000, 4000) = 4000.

        aggressiveness = 1.0
        current_time = 100

        # Call method
        self.manager._manage_automation(
            self.mock_firm,
            aggressiveness,
            self.mock_guidance,
            current_time,
            government=self.mock_government
        )

        # Verify Logic
        # 1. Firm assets decreased by spend (4000) AND tax (4000 * 0.05 = 200)
        # However, mocks don't automatically subtract unless side_effect logic is added.
        # But we can check if assets were modified.
        # Wait, the code does firm.assets -= actual_spend.
        # Mocks track assignments if it's a PropertyMock, but standard Mock attributes just store values.
        # Since I didn't set up specific side effects for subtraction, checking the exact value is hard
        # unless the implementation does `firm.assets = firm.assets - x`.

        # Better verification: Check if government.collect_tax was called with expected amount.
        expected_tax = 4000.0 * 0.05 # 200.0
        self.mock_government.collect_tax.assert_called_with(expected_tax, "automation_tax", 1, current_time)

if __name__ == '__main__':
    unittest.main()
