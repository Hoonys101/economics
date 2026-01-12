
import unittest
import numpy as np
from simulation.metrics.mobility_tracker import MobilityTracker

class TestMobilityTracker(unittest.TestCase):
    def test_ige_calculation_perfect_correlation(self):
        tracker = MobilityTracker()
        # Perfect correlation: Child = Parent * 2
        for i in range(1, 100):
            tracker.register_birth(i, i+100, float(i*100))
            tracker.record_final_wealth(i+100, float(i*200)) # 2x wealth

        ige = tracker.calculate_ige()
        r2 = tracker.calculate_r_squared()

        # Log(2*X) = Log(2) + 1 * Log(X)
        # Slope (Beta) should be 1.0
        # Relaxed precision due to log(x+1) bias at lower values
        self.assertAlmostEqual(ige, 1.0, places=1)
        self.assertAlmostEqual(r2, 1.0, places=1)

    def test_ige_calculation_no_correlation(self):
        tracker = MobilityTracker()
        # No correlation: Child wealth random
        np.random.seed(42)
        for i in range(1, 1000):
            parent_wealth = np.random.uniform(100, 1000)
            child_wealth = np.random.uniform(100, 1000)
            tracker.register_birth(i, i+1000, parent_wealth)
            tracker.record_final_wealth(i+1000, child_wealth)

        ige = tracker.calculate_ige()
        r2 = tracker.calculate_r_squared()

        # IGE should be close to 0
        self.assertLess(abs(ige), 0.1)
        self.assertLess(r2, 0.1)

    def test_ige_calculation_meritocracy(self):
        tracker = MobilityTracker()
        # High Meritocracy: Child wealth depends more on random talent than parent wealth
        # Child = Parent^0.1 * Random
        for i in range(1, 100):
            parent_w = float(i * 100)
            child_w = (parent_w ** 0.1) * 1000.0
            tracker.register_birth(i, i+100, parent_w)
            tracker.record_final_wealth(i+100, child_w)

        ige = tracker.calculate_ige()
        # Slope should be approx 0.1
        self.assertAlmostEqual(ige, 0.1, places=1)

if __name__ == '__main__':
    unittest.main()
