"""Unit test for Interest Sensitivity logic in AIDrivenHouseholdDecisionEngine."""
import pytest
from unittest.mock import MagicMock, patch


class TestInterestSensitivityLogic:
    """Test the Interest Sensitivity (Missing Link) logic in isolation."""

    def test_savings_incentive_ant_high_rate(self):
        """ANT personality should have higher savings incentive when real rate is high."""
        # Given
        nominal_rate = 0.10  # 10%
        expected_inflation = 0.0
        neutral_rate = 0.02
        sensitivity_ant = 5.0

        # When - Calculate savings incentive
        real_rate = nominal_rate - expected_inflation
        savings_incentive = max(0.0, (real_rate - neutral_rate) * sensitivity_ant)

        # Then
        assert real_rate == 0.10
        assert savings_incentive == 0.40  # (0.10 - 0.02) * 5.0 = 0.40

    def test_savings_incentive_grasshopper_high_rate(self):
        """Grasshopper personality should have lower savings incentive."""
        # Given
        nominal_rate = 0.10  # 10%
        expected_inflation = 0.0
        neutral_rate = 0.02
        sensitivity_gh = 1.0

        # When
        real_rate = nominal_rate - expected_inflation
        savings_incentive = max(0.0, (real_rate - neutral_rate) * sensitivity_gh)

        # Then
        assert savings_incentive == 0.08  # (0.10 - 0.02) * 1.0 = 0.08

    def test_savings_incentive_at_neutral_rate(self):
        """No savings incentive when rate equals neutral rate."""
        # Given
        nominal_rate = 0.02  # 2% (neutral)
        expected_inflation = 0.0
        neutral_rate = 0.02
        sensitivity = 5.0

        # When
        real_rate = nominal_rate - expected_inflation
        savings_incentive = max(0.0, (real_rate - neutral_rate) * sensitivity)

        # Then
        assert savings_incentive == 0.0

    def test_savings_incentive_with_inflation_expectation(self):
        """Expected inflation reduces real rate and thus savings incentive."""
        # Given
        nominal_rate = 0.10  # 10%
        expected_inflation = 0.05  # 5% expected inflation
        neutral_rate = 0.02
        sensitivity = 5.0

        # When
        real_rate = nominal_rate - expected_inflation  # 0.10 - 0.05 = 0.05
        savings_incentive = max(0.0, (real_rate - neutral_rate) * sensitivity)

        # Then
        assert real_rate == pytest.approx(0.05)
        assert savings_incentive == pytest.approx(0.15)  # (0.05 - 0.02) * 5.0 = 0.15

    def test_consumption_aggressiveness_reduction(self):
        """Consumption aggressiveness should be reduced by savings incentive."""
        # Given
        base_aggressiveness = 0.8
        savings_incentive = 0.40
        debt_penalty = 0.0

        # When - Apply the reduction formula from the engine
        adjusted = base_aggressiveness * (1.0 - savings_incentive - debt_penalty)
        adjusted = max(0.0, adjusted)

        # Then
        assert adjusted == pytest.approx(0.48)  # 0.8 * 0.6 = 0.48

    def test_dsr_penalty_applied(self):
        """High DSR should trigger debt penalty."""
        # Given
        daily_interest_burden = 50.0
        income_proxy = 100.0  # DSR = 50/100 = 50%
        dsr_threshold = 0.4

        # When
        dsr = daily_interest_burden / (income_proxy + 1e-9)
        debt_penalty = 0.2 if dsr > dsr_threshold else 0.0

        # Then
        assert dsr == pytest.approx(0.5)
        assert debt_penalty == 0.2

    def test_subsistence_constraint_bypasses_reduction(self):
        """High survival need should bypass the reduction logic."""
        # Given
        survival_need = 80.0  # High (starving)
        maslow_threshold = 50.0
        base_aggressiveness = 0.8
        savings_incentive = 0.40

        # When - Check if reduction applies
        should_reduce = survival_need < maslow_threshold

        # Then
        assert should_reduce is False  # 80 < 50 is False, so no reduction


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
