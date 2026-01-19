import pytest
from modules.finance.domain.corporate_finance import AltmanZScoreCalculator

class TestAltmanZScoreCalculator:

    def test_calculate_safe_zone(self):
        """Test a scenario where the firm is clearly safe (Z > 3.0)."""
        # Example:
        # Assets = 1000
        # WC = 400 (40%) -> 1.2 * 0.4 = 0.48
        # RE = 500 (50%) -> 1.4 * 0.5 = 0.70
        # EBIT = 600 (60%) -> 3.3 * 0.6 = 1.98
        # Total Z = 0.48 + 0.70 + 1.98 = 3.16

        z = AltmanZScoreCalculator.calculate(
            total_assets=1000.0,
            working_capital=400.0,
            retained_earnings=500.0,
            average_profit=600.0
        )
        assert z == pytest.approx(3.16, abs=0.01)

    def test_calculate_distress_zone(self):
        """Test a scenario where the firm is in distress (Z < 1.8)."""
        # Example:
        # Assets = 1000
        # WC = 100 (10%) -> 1.2 * 0.1 = 0.12
        # RE = 0 (0%) -> 0
        # EBIT = 100 (10%) -> 3.3 * 0.1 = 0.33
        # Total Z = 0.12 + 0.33 = 0.45

        z = AltmanZScoreCalculator.calculate(
            total_assets=1000.0,
            working_capital=100.0,
            retained_earnings=0.0,
            average_profit=100.0
        )
        assert z == pytest.approx(0.45, abs=0.01)

    def test_calculate_zero_assets(self):
        """Test calculation with zero assets (should handle division by zero)."""
        z = AltmanZScoreCalculator.calculate(
            total_assets=0.0,
            working_capital=0.0,
            retained_earnings=0.0,
            average_profit=0.0
        )
        assert z == 0.0

    def test_calculate_negative_values(self):
        """Test calculation with negative working capital or profit."""
        # Assets = 1000
        # WC = -100 (-10%) -> 1.2 * -0.1 = -0.12
        # RE = -200 (-20%) -> 1.4 * -0.2 = -0.28
        # EBIT = -100 (-10%) -> 3.3 * -0.1 = -0.33
        # Total Z = -0.73

        z = AltmanZScoreCalculator.calculate(
            total_assets=1000.0,
            working_capital=-100.0,
            retained_earnings=-200.0,
            average_profit=-100.0
        )
        assert z == pytest.approx(-0.73, abs=0.01)
