import unittest
from unittest.mock import MagicMock
from simulation.systems.social_system import SocialSystem
from simulation.core_agents import Household
from simulation.decisions.housing_manager import HousingManager

class TestSocialSystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.system = SocialSystem(self.config)
        self.households = [
            MagicMock(spec=Household, id=1, current_consumption=100.0, is_active=True),
            MagicMock(spec=Household, id=2, current_consumption=50.0, is_active=True),
            MagicMock(spec=Household, id=3, current_consumption=10.0, is_active=True)
        ]
        self.housing_manager = MagicMock(spec=HousingManager)
        self.housing_manager.get_housing_tier.side_effect = lambda h: 1 if h.id == 1 else (2 if h.id == 2 else 3)
        # Tiers: 1 (High), 2 (Mid), 3 (Low) usually.
        # But logic says score = tier * 1000.
        # If tier 1 is better, usually score should be higher?
        # Simulation logic: housing_score = housing_tier * 1000.0
        # Wait, usually Tier 1 is top?
        # HousingManager.get_housing_tier usually returns 1, 2, 3.
        # If score is tier*1000, then Tier 3 gets 3000 points, Tier 1 gets 1000.
        # So Higher Tier Number = Higher Score = Higher Rank?
        # That implies Tier 3 is "Better" or just different.
        # Let's assume the system logic is correct and test that it sorts correctly.

    def test_update_social_ranks(self):
        context = {
            "households": self.households,
            "housing_manager": self.housing_manager
        }

        # Scores:
        # H1: 100*10 + 1*1000 = 2000 (Wait, 1000+1000 = 2000)
        # H2: 50*10 + 2*1000 = 2500
        # H3: 10*10 + 3*1000 = 3100

        # Sorted (Reverse=True): H3 (3100), H2 (2500), H1 (2000)
        # Ranks:
        # H3: Rank 0 -> Percentile 1.0
        # H2: Rank 1 -> Percentile 0.66
        # H1: Rank 2 -> Percentile 0.33

        self.system.update_social_ranks(context)

        self.assertEqual(self.households[2].social_rank, 1.0)
        self.assertAlmostEqual(self.households[1].social_rank, 1.0 - 1/3)
        self.assertAlmostEqual(self.households[0].social_rank, 1.0 - 2/3)

    def test_calculate_reference_standard(self):
        # Set social ranks manually for this test
        self.households[0].social_rank = 1.0 # Top
        self.households[1].social_rank = 0.5
        self.households[2].social_rank = 0.0

        context = {
            "households": self.households,
            "housing_manager": self.housing_manager
        }

        # Top 20% of 3 is 1 household (max(1, 0.6) = 1)
        # So only H1 is in top 20%.

        ref = self.system.calculate_reference_standard(context)

        self.assertEqual(ref["avg_consumption"], 100.0)
        self.assertEqual(ref["avg_housing_tier"], 1)

if __name__ == '__main__':
    unittest.main()
