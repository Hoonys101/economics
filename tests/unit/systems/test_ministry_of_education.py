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
        h = MagicMock()
        h.id = id
        # Mock wallet balance for sorting (required by Ministry)
        h._econ_state.wallet.get_balance.return_value = float(assets)
        h._econ_state.assets = assets
        h._econ_state.education_level = edu_level
        h._econ_state.aptitude = aptitude
        h._bio_state.is_active = is_active
        h.__class__.__name__ = "Household"
        return h

    def test_run_public_education_basic_grant_legacy(self):
        # Verification of Transactions instead of direct transfers
        households = [
            self._create_household(101, 500, 0, 0.5), # Eligible for basic
            self._create_household(102, 1000, 1, 0.6) # Already has basic
        ]

        transactions = self.ministry.run_public_education(households, self.mock_government, 1)

        # 1 eligible, 1 not
        self.assertEqual(len(transactions), 1)
        tx = transactions[0]
        self.assertEqual(tx.buyer_id, self.mock_government.id)
        self.assertEqual(tx.item_id, "education_level_1")
        self.assertEqual(tx.price, 100) # Cost for Level 1

    def test_run_public_education_basic_grant_settlement(self):
        # Same logic, verifying transactions are generated
        households = [
            self._create_household(101, 500, 0, 0.5),
        ]

        transactions = self.ministry.run_public_education(households, self.mock_government, 1)

        # Verify Transaction
        self.assertEqual(len(transactions), 1)
        tx = transactions[0]
        self.assertEqual(tx.buyer_id, self.mock_government.id)
        self.assertEqual(tx.price, 100)

    def test_run_public_education_scholarship_settlement(self):
        # Add dummy rich households to ensure percentile logic works
        households = [
            self._create_household(101, 150, 1, 0.9),   # Eligible (Poor & Smart)
            self._create_household(102, 1000, 1, 0.5),
            self._create_household(103, 1000, 1, 0.5),
            self._create_household(104, 1000, 1, 0.5),
            self._create_household(105, 1000, 1, 0.5),
        ]

        cost = self.mock_config.EDUCATION_COST_PER_LEVEL[2] # 500
        subsidy = cost * 0.8
        student_share = cost * 0.2

        transactions = self.ministry.run_public_education(households, self.mock_government, 1)

        # Verify Transactions
        # 1. Subsidy (Gov -> Teacher)
        # 2. Tuition (Student -> Teacher)
        self.assertEqual(len(transactions), 2)

        tx_subsidy = transactions[0]
        self.assertEqual(tx_subsidy.buyer_id, self.mock_government.id)
        self.assertEqual(tx_subsidy.price, subsidy)

        tx_student = transactions[1]
        self.assertEqual(tx_student.buyer_id, households[0].id)
        self.assertEqual(tx_student.price, student_share)

    def test_budget_constraints(self):
        # Government has 10k assets, budget is 10% = 1k
        # Basic edu costs 100 each. 11 households want it. Only 10 should get it.
        households = [self._create_household(i, 500, 0, 0.5) for i in range(11)]

        transactions = self.ministry.run_public_education(households, self.mock_government, 1)

        # Max budget 1000 / cost 100 = 10 grants
        self.assertEqual(len(transactions), 10)


if __name__ == '__main__':
    unittest.main()
