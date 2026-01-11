import unittest
from unittest.mock import Mock, MagicMock
from simulation.decisions.housing_manager import HousingManager

class TestHousingDecision(unittest.TestCase):
    def setUp(self):
        self.mock_agent = Mock()
        self.mock_agent.optimism = 0.5
        self.mock_agent.ambition = 0.5
        # Mock specific attributes required by HousingManager
        self.mock_agent.is_homeless = False
        self.mock_agent.residing_property_id = 1

        self.mock_config = Mock()
        self.mock_config.MAINTENANCE_RATE_PER_TICK = 0.001
        self.mock_config.ENABLE_VANITY_SYSTEM = True
        self.mock_config.MIMICRY_FACTOR = 0.5

        self.housing_manager = HousingManager(self.mock_agent, self.mock_config)

    def test_should_buy_high_interest_preference_rent(self):
        """
        Test Case A: High Interest Rate (15%)
        High opportunity cost of down payment + High mortgage rates should favor RENTING.
        """
        property_value = 100000.0
        rent_price = 500.0
        risk_free_rate = 0.15 # 15% annual

        # Expected: False (Rent is better)
        decision = self.housing_manager.should_buy(
            property_value=property_value,
            rent_price=rent_price,
            risk_free_rate=risk_free_rate
        )
        self.assertFalse(decision, "Should prefer RENTING when interest rates are high (15%)")

    def test_should_buy_low_interest_preference_buy(self):
        """
        Test Case B: Low Interest Rate (1%)
        Low opportunity cost + Cheap leverage should favor BUYING.
        """
        property_value = 100000.0
        rent_price = 600.0 # Slightly higher rent to make buying even more attractive/comparable
        risk_free_rate = 0.01 # 1% annual

        # Expected: True (Buy is better)
        decision = self.housing_manager.should_buy(
            property_value=property_value,
            rent_price=rent_price,
            risk_free_rate=risk_free_rate
        )
        self.assertTrue(decision, "Should prefer BUYING when interest rates are low (1%)")

if __name__ == '__main__':
    unittest.main()
