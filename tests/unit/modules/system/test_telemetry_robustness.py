import unittest
from unittest.mock import Mock
from modules.system.telemetry import TelemetryCollector

class MockRegistry:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)

class TestTelemetryRobustness(unittest.TestCase):
    def test_flat_key_resolution(self):
        """
        Verify that TelemetryCollector can resolve flat keys like 'government.tax_rate'
        even if 'government' object doesn't exist.
        """
        # Registry has flat keys
        data = {
            "government.tax_rate": 0.25,
            "finance.base_rate": 0.05
        }
        registry = MockRegistry(data)
        collector = TelemetryCollector(registry)

        # Subscribe using full key
        collector.subscribe(["government.tax_rate"], frequency_interval=1)

        # Harvest
        snapshot = collector.harvest(1)

        self.assertIn("government.tax_rate", snapshot.data)
        self.assertEqual(snapshot.data["government.tax_rate"], 0.25)
        self.assertEqual(len(snapshot.errors), 0)

    def test_mixed_resolution(self):
        """
        Verify mixed usage: Flat keys and Object traversal.
        """
        class Gov:
            def __init__(self):
                self.policy = "growth"

        data = {
            "government.tax_rate": 0.25, # Flat key
            "government": Gov()          # Object key
        }
        registry = MockRegistry(data)
        collector = TelemetryCollector(registry)

        # Subscribe
        collector.subscribe(["government.tax_rate"]) # Should prefer flat key if exists?
        # Strategy 1 checks full key first. So it gets 0.25.

        collector.subscribe(["government.policy"])   # Should fallback to object traversal

        snapshot = collector.harvest(1)

        self.assertEqual(snapshot.data["government.tax_rate"], 0.25)
        self.assertEqual(snapshot.data["government.policy"], "growth")
