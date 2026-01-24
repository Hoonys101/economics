import unittest
from unittest.mock import Mock, MagicMock
from simulation.systems.ministry_of_education import MinistryOfEducation

class TestMinistryOfEducation(unittest.TestCase):

    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.PUBLIC_EDU_BUDGET_RATIO = 0.10
        self.mock_config.SCHOLARSHIP_WEALTH_PERCENTILE = 0.20
        self.mock_config.EDUCATION_COST_PER_LEVEL = {1: 100, 2: 500}
        self.mock_config.SCHOLARSHIP_POTENTIAL_THRESHOLD = 0.8

        self.ministry = MinistryOfEducation(self.mock_config)

        self.mock_government = MagicMock()
        self.mock_government._assets = 10000
        self.mock_government.revenue_this_tick = 10000  # Simulate 10k revenue for budget calcs
        self.mock_government.id = 1
        self.mock_government.expenditure_this_tick = 0
        self.mock_government.total_money_issued = 0
        self.mock_government.current_tick_stats = {"education_spending": 0}

    def _create_household(self, id, assets, edu_level, aptitude, is_active=True):
        h = Mock()
        h.id = id
        h.assets = assets # Fix: Set assets property directly
        h.education_level = edu_level
        h.aptitude = aptitude
        h.is_active = is_active
        h.__class__.__name__ = "Household"
        return h

    def test_run_public_education_basic_grant_legacy(self):
        # Legacy Mode (No SettlementSystem)
        households = [
            self._create_household(101, 500, 0, 0.5), # Eligible for basic
            self._create_household(102, 1000, 1, 0.6) # Already has basic
        ]

        initial_gov_assets = self.mock_government._assets # Use backing field for check
        cost = self.mock_config.EDUCATION_COST_PER_LEVEL[1] # 100

        self.ministry.run_public_education(households, self.mock_government, 1)

        self.assertEqual(households[0].education_level, 1)
        self.assertEqual(households[1].education_level, 1) # Unchanged

        # Check Legacy Behavior
        self.mock_government._sub_assets.assert_called_with(cost)

        self.assertEqual(self.mock_government.expenditure_this_tick, cost)
        self.assertEqual(self.mock_government.current_tick_stats["education_spending"], cost)

    def test_run_public_education_basic_grant_settlement(self):
        # New Mode (With SettlementSystem)
        households = [
            self._create_household(101, 500, 0, 0.5),
        ]

        mock_settlement = MagicMock()
        mock_settlement.transfer.return_value = True
        mock_reflux = MagicMock()

        cost = self.mock_config.EDUCATION_COST_PER_LEVEL[1] # 100

        self.ministry.run_public_education(households, self.mock_government, 1,
                                           reflux_system=mock_reflux,
                                           settlement_system=mock_settlement)

        self.assertEqual(households[0].education_level, 1)

        # Verify Transfer called
        mock_settlement.transfer.assert_called_once()
        args = mock_settlement.transfer.call_args[0]
        # (government, reflux, cost, memo)
        self.assertEqual(args[0], self.mock_government)
        self.assertEqual(args[1], mock_reflux)
        self.assertEqual(args[2], cost)

        # Verify Legacy NOT called
        self.mock_government._sub_assets.assert_not_called()

    def test_run_public_education_scholarship_settlement(self):
        # Add dummy rich households to ensure percentile logic works
        households = [
            self._create_household(101, 150, 1, 0.9),   # Eligible (Poor & Smart)
            self._create_household(102, 1000, 1, 0.5),
            self._create_household(103, 1000, 1, 0.5),
            self._create_household(104, 1000, 1, 0.5),
            self._create_household(105, 1000, 1, 0.5),
        ]

        mock_settlement = MagicMock()
        mock_settlement.transfer.return_value = True
        mock_reflux = MagicMock()

        cost = self.mock_config.EDUCATION_COST_PER_LEVEL[2] # 500
        subsidy = cost * 0.8
        student_share = cost * 0.2

        self.ministry.run_public_education(households, self.mock_government, 1,
                                           reflux_system=mock_reflux,
                                           settlement_system=mock_settlement)

        self.assertEqual(households[0].education_level, 2)

        # Verify Transfers
        # 1. Subsidy (Gov -> Reflux)
        # 2. Tuition (Student -> Reflux)
        self.assertEqual(mock_settlement.transfer.call_count, 2)

        # Check args
        calls = mock_settlement.transfer.call_args_list
        # Call 1: Subsidy
        self.assertEqual(calls[0][0][0], self.mock_government)
        self.assertEqual(calls[0][0][2], subsidy)

        # Call 2: Tuition
        self.assertEqual(calls[1][0][0], households[0])
        self.assertEqual(calls[1][0][2], student_share)

    def test_budget_constraints(self):
        # Government has 10k assets, budget is 10% = 1k
        # Basic edu costs 100 each. 11 households want it. Only 10 should get it.
        households = [self._create_household(i, 500, 0, 0.5) for i in range(11)]

        # Use legacy mode for simplicity in this check, or new mode with mock transfer
        # Since logic is shared until execution, legacy is fine for counting promotions.
        self.ministry.run_public_education(households, self.mock_government, 1)

        promoted_count = sum(1 for h in households if h.education_level == 1)
        self.assertEqual(promoted_count, 10)

        # Check assets (legacy behavior)
        expected_spent = 10 * 100
        self.mock_government._sub_assets.assert_called()
        self.assertEqual(self.mock_government.expenditure_this_tick, expected_spent)


if __name__ == '__main__':
    unittest.main()
