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
        self.mock_government.revenue_this_tick = (
            10000  # Simulate 10k revenue for budget calcs
        )
        self.mock_government.id = 1
        self.mock_government.expenditure_this_tick = 0
        self.mock_government.total_money_issued = 0
        self.mock_government.current_tick_stats = {"education_spending": 0}

    def _create_household(self, id, assets, edu_level, aptitude, is_active=True):
        h = Mock()
        h.id = id
        h._assets = assets
        h.education_level = edu_level
        h.aptitude = aptitude
        h.is_active = is_active
        h.__class__.__name__ = "Household"
        return h

    def test_run_public_education_basic_grant(self):
        households = [
            self._create_household(101, 500, 0, 0.5),  # Eligible for basic
            self._create_household(102, 1000, 1, 0.6),  # Already has basic
        ]

        initial_gov_assets = self.mock_government.assets
        cost = self.mock_config.EDUCATION_COST_PER_LEVEL[1]  # 100

        self.ministry.run_public_education(households, self.mock_government, 1)

        self.assertEqual(households[0].education_level, 1)
        self.assertEqual(households[1].education_level, 1)  # Unchanged
        self.assertEqual(self.mock_government.assets, initial_gov_assets - cost)
        self.assertEqual(self.mock_government.expenditure_this_tick, cost)
        self.assertEqual(
            self.mock_government.current_tick_stats["education_spending"], cost
        )

    def test_run_public_education_scholarship(self):
        # With 5 active households, the bottom 20% is the single poorest one.
        households = [
            self._create_household(
                101, 150, 1, 0.9
            ),  # Poorest, high potential -> Eligible
            self._create_household(102, 200, 1, 0.7),  # 2nd poorest
            self._create_household(103, 300, 1, 0.6),  # Middle class
            self._create_household(104, 400, 1, 0.5),  # Middle class
            self._create_household(105, 10000, 1, 0.9),  # Rich, high potential
            self._create_household(
                106, 80, 1, 0.85, is_active=False
            ),  # Inactive -> Ignored
        ]

        initial_gov_assets = self.mock_government.assets
        cost = self.mock_config.EDUCATION_COST_PER_LEVEL[2]  # 500
        subsidy = cost * 0.8
        student_share = cost * 0.2

        # Ensure the target household can pay its share
        self.assertTrue(households[0].assets >= student_share)

        self.ministry.run_public_education(households, self.mock_government, 1)

        # Check that the eligible household was promoted
        self.assertEqual(households[0].education_level, 2)
        self.assertEqual(households[0].assets, 150 - student_share)
        self.assertEqual(self.mock_government.assets, initial_gov_assets - subsidy)
        self.assertEqual(self.mock_government.expenditure_this_tick, subsidy)

        # Check that other households were not promoted
        self.assertEqual(households[1].education_level, 1)
        self.assertEqual(households[4].education_level, 1)

    def test_budget_constraints(self):
        # Government has 10k assets, budget is 10% = 1k
        # Basic edu costs 100 each. 11 households want it. Only 10 should get it.
        households = [self._create_household(i, 500, 0, 0.5) for i in range(11)]

        self.ministry.run_public_education(households, self.mock_government, 1)

        promoted_count = sum(1 for h in households if h.education_level == 1)
        self.assertEqual(promoted_count, 10)
        self.assertEqual(self.mock_government.assets, 10000 - (10 * 100))


if __name__ == "__main__":
    unittest.main()
