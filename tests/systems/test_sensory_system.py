import unittest
from unittest.mock import MagicMock
from simulation.systems.sensory_system import SensorySystem
from simulation.systems.api import SensoryContext

class TestSensorySystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.system = SensorySystem(self.config)

    def test_generate_government_sensory_dto(self):
        tracker = MagicMock()
        government = MagicMock()
        government.approval_rating = 0.6

        # Mock latest indicators
        tracker.get_latest_indicators.return_value = {
            "avg_goods_price": 12.0, # Last was 10.0 default. Inflation = (12-10)/10 = 0.2
            "unemployment_rate": 0.05,
            "total_production": 110.0, # Last was 0.0 default? No, last_gdp_for_sma defaults to 0.0
            "avg_wage": 20.0
        }

        # Set initial last_gdp to something non-zero to avoid div by zero if handled,
        # or check how logic handles it. Logic: (current - last) / last if last > 0 else 0.0
        # Default last_gdp is 0.0. So first growth is 0.0.
        self.system.last_gdp_for_sma = 100.0

        context: SensoryContext = {
            'tracker': tracker,
            'government': government,
            'time': 1
        }

        dto = self.system.generate_government_sensory_dto(context)

        # Verify Buffers
        self.assertEqual(len(self.system.inflation_buffer), 1)
        self.assertAlmostEqual(self.system.inflation_buffer[0], 0.2)

        # GDP Growth: (110 - 100) / 100 = 0.1
        self.assertAlmostEqual(self.system.gdp_growth_buffer[0], 0.1)

        # DTO values (SMA of 1 item is the item value)
        self.assertEqual(dto.tick, 1)
        self.assertAlmostEqual(dto.inflation_sma, 0.2)
        self.assertAlmostEqual(dto.gdp_growth_sma, 0.1)
        self.assertAlmostEqual(dto.unemployment_sma, 0.05)
        self.assertAlmostEqual(dto.approval_sma, 0.6)
