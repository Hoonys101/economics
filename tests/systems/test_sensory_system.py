import unittest
from unittest.mock import MagicMock
from simulation.systems.sensory_system import SensorySystem

class TestSensorySystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.system = SensorySystem(self.config)
        self.tracker = MagicMock()
        self.government = MagicMock()
        self.government.approval_rating = 0.8

    def test_generate_sensory_dto(self):
        # Mock tracker return
        self.tracker.get_latest_indicators.return_value = {
            "avg_goods_price": 11.0, # 10% inflation from default 10.0
            "unemployment_rate": 0.05,
            "total_production": 100.0,
            "avg_wage": 20.0
        }

        context = {
            "tracker": self.tracker,
            "government": self.government,
            "time": 1
        }

        dto = self.system.generate_government_sensory_dto(context)

        self.assertEqual(dto.tick, 1)
        self.assertAlmostEqual(dto.inflation_sma, 0.1) # (11-10)/10
        self.assertEqual(dto.unemployment_sma, 0.05)
        self.assertEqual(dto.gdp_growth_sma, 0.0) # Initial GDP was 0, but division by zero check?
        # Logic: if last_gdp > 0 else 0.0. last_gdp starts at 0.0.
        # So growth should be 0.0.
        self.assertEqual(dto.wage_sma, 20.0)
        self.assertEqual(dto.approval_sma, 0.8)

        # Second tick
        self.tracker.get_latest_indicators.return_value = {
            "avg_goods_price": 12.1, # 10% inflation from 11.0
            "unemployment_rate": 0.05,
            "total_production": 110.0, # 10% growth from 100.0
            "avg_wage": 22.0
        }

        context["time"] = 2
        dto2 = self.system.generate_government_sensory_dto(context)

        self.assertAlmostEqual(dto2.inflation_sma, 0.1) # Avg of 0.1 and 0.1
        self.assertAlmostEqual(dto2.gdp_growth_sma, 0.05) # Avg of 0.0 and 0.1 (Growth from 100 to 110 is 0.1)
        # Wait, last_gdp was updated to 100.0 in first call? Yes.
        # So growth = (110-100)/100 = 0.1.
        # Buffer has [0.0, 0.1]. SMA = 0.05. Correct.

if __name__ == '__main__':
    unittest.main()
