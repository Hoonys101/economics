import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure the root directory is in sys.path so we can import simulation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.interface import dashboard_connector

class TestDashboardConnector(unittest.TestCase):

    @patch('simulation.interface.dashboard_connector.simulation_main.create_simulation')
    def test_get_engine_instance(self, mock_create):
        """Verify get_engine_instance returns the factory result."""
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        result = dashboard_connector.get_engine_instance()

        mock_create.assert_called_once()
        self.assertEqual(result, mock_engine)

    def test_run_tick(self):
        """Verify run_tick advances time and returns int."""
        mock_engine = MagicMock()
        # Mocking time attribute. Initially it might be 9, after run_tick it stays same object but we simulate effect if needed.
        # However, the connector just returns simulation.time.
        # Let's say engine.time is 10.
        mock_engine.time = 10

        result = dashboard_connector.run_tick(mock_engine)

        mock_engine.run_tick.assert_called_once()
        self.assertEqual(result, 10)
        self.assertIsInstance(result, int)

    def test_get_metrics_keys(self):
        """Verify get_metrics returns required keys and correct calculation logic."""
        mock_engine = MagicMock()
        mock_engine.time = 5

        # Setup households: 2 active households
        h1 = MagicMock()
        h1.is_active = True
        h1.assets = 1000.0

        h2 = MagicMock()
        h2.is_active = True
        h2.assets = 2000.0

        # In the actual code, it iterates over simulation.households.
        # We need to make sure the list comprehension works.
        mock_engine.households = [h1, h2]

        # Setup tracker indicators
        mock_engine.tracker.get_latest_indicators.return_value = {
            "total_production": 500.0,
            "unemployment_rate": 5.0,
            "inflation_rate": 0.02,
            "total_consumption": 450.0
        }

        result = dashboard_connector.get_metrics(mock_engine)

        required_keys = ['tick', 'total_population', 'gdp', 'average_assets', 'unemployment_rate']
        for key in required_keys:
            self.assertIn(key, result)

        # Validate values
        self.assertEqual(result['tick'], 5)
        self.assertEqual(result['total_population'], 2)
        self.assertEqual(result['gdp'], 500.0)
        self.assertEqual(result['unemployment_rate'], 5.0)

        # Validate Average Assets Calculation: (1000 + 2000) / 2 = 1500
        self.assertEqual(result['average_assets'], 1500.0)

if __name__ == '__main__':
    unittest.main()
