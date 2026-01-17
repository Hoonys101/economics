import unittest
from unittest.mock import MagicMock
from simulation.systems.social_system import SocialSystem
from simulation.systems.api import SocialMobilityContext

class TestSocialSystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.system = SocialSystem(self.config)
        self.housing_manager = MagicMock()

    def test_update_social_ranks(self):
        # Create mock households
        h1 = MagicMock()
        h1.id = 1
        h1.is_active = True
        h1.current_consumption = 100.0

        h2 = MagicMock()
        h2.id = 2
        h2.is_active = True
        h2.current_consumption = 50.0

        h3 = MagicMock()
        h3.id = 3
        h3.is_active = True
        h3.current_consumption = 200.0

        households = [h1, h2, h3]

        # Mock housing tier
        self.housing_manager.get_housing_tier.side_effect = lambda h: 1.0 # All same tier

        context: SocialMobilityContext = {
            'households': households,
            'housing_manager': self.housing_manager
        }

        self.system.update_social_ranks(context)

        # Expected scores:
        # h1: 100*10 + 1000 = 2000
        # h2: 50*10 + 1000 = 1500
        # h3: 200*10 + 1000 = 3000
        # Sorted: h3 (Top), h1, h2 (Bottom)

        # Ranks:
        # h3: index 0, percentile = 1.0 - 0/3 = 1.0
        # h1: index 1, percentile = 1.0 - 1/3 = 0.666
        # h2: index 2, percentile = 1.0 - 2/3 = 0.333

        self.assertEqual(h3.social_rank, 1.0)
        self.assertAlmostEqual(h1.social_rank, 0.666, places=2)
        self.assertAlmostEqual(h2.social_rank, 0.333, places=2)

    def test_calculate_reference_standard(self):
        # Create mock households with ranks
        active_households = []
        for i in range(10):
            h = MagicMock()
            h.id = i
            h.is_active = True
            h.social_rank = float(i) / 9.0 # 0.0 to 1.0
            h.current_consumption = 100.0 * (i + 1)
            active_households.append(h)

        # Top 20% of 10 is 2.
        # Sorted by rank desc: h9 (rank 1.0), h8 (rank 0.88), ...
        # Top 2 are h9 and h8.
        # h9 consumption: 1000
        # h8 consumption: 900
        # Avg consumption: 950

        # Mock housing manager
        self.housing_manager.get_housing_tier.return_value = 2.0

        context: SocialMobilityContext = {
            'households': active_households,
            'housing_manager': self.housing_manager
        }

        result = self.system.calculate_reference_standard(context)

        self.assertEqual(result['avg_consumption'], 950.0)
        self.assertEqual(result['avg_housing_tier'], 2.0)
