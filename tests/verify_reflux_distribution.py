
import unittest
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

from simulation.systems.reflux_system import EconomicRefluxSystem

# Mocks
@dataclass
class MockHousehold:
    id: int
    is_active: bool = True
    assets: float = 0.0
    labor_income_this_tick: float = 0.0
    income_history: Dict[str, float] = field(default_factory=dict)

    def _add_assets(self, amount: float):
        self.assets += amount

class TestRefluxSystem(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        self.reflux = EconomicRefluxSystem()

    def test_distribute_exact_division(self):
        self.reflux.balance = 5000.0
        households = [MockHousehold(id=i) for i in range(100)]

        self.reflux.distribute(households)

        expected = 50.0
        for h in households:
            self.assertEqual(h.assets, expected)
            self.assertEqual(h.labor_income_this_tick, expected)

        self.assertEqual(self.reflux.balance, 0.0)

    def test_distribute_prime_division(self):
        self.reflux.balance = 5000.0
        # 3 households. 5000 / 3 = 1666.6666666666667
        households = [MockHousehold(id=i) for i in range(3)]

        self.reflux.distribute(households)

        total_distributed = sum(h.assets for h in households)
        self.assertAlmostEqual(total_distributed, 5000.0, places=10)
        self.assertEqual(self.reflux.balance, 0.0)

        # Check first 2 got same amount
        self.assertEqual(households[0].assets, households[1].assets)

        # Check remainder handling (Last one gets rest)
        # 1666.6666666666667 * 2 = 3333.3333333333335
        # 5000 - 3333... = 1666.6666666666665
        # Difference should be extremely small (machine epsilon)
        diff = households[2].assets - households[0].assets
        print(f"Diff between last and first: {diff}")
        self.assertTrue(abs(diff) < 1e-10)

    def test_distribute_with_drift_amount(self):
        # Test with the drift amount observed in logs
        self.reflux.balance = 299.7760
        households = [MockHousehold(id=i) for i in range(3)]

        self.reflux.distribute(households)

        total = sum(h.assets for h in households)
        self.assertAlmostEqual(total, 299.7760, places=10)
        self.assertEqual(self.reflux.balance, 0.0)

if __name__ == '__main__':
    unittest.main()
