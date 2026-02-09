import unittest
from collections import deque
from unittest.mock import MagicMock, Mock
from simulation.systems.sensory_system import SensorySystem
from modules.simulation.api import ISensoryDataProvider, AgentSensorySnapshotDTO, AgentStateDTO

class MockAgent:
    def __init__(self, is_active, wealth, approval):
        self.is_active = is_active
        self.wealth = wealth
        self.approval = approval

    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        return {
            "is_active": self.is_active,
            "total_wealth": self.wealth,
            "approval_rating": self.approval
        }

class MockInequalityTracker:
    def calculate_gini_coefficient(self, assets):
        # Simplified Gini for testing: just return 0.5 or something deterministic if list is not empty
        return 0.3 if assets else 0.0

class TestSensoryPurity(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.system = SensorySystem(self.config)
        self.tracker = MagicMock()
        self.tracker.get_latest_indicators.return_value = {
            "avg_goods_price": 10.0,
            "unemployment_rate": 0.05,
            "total_production": 1000.0,
            "avg_wage": 20.0
        }
        self.government = MagicMock()
        self.government.approval_rating = 0.6

    def test_generate_government_sensory_dto_purity(self):
        # Setup context
        households = [
            MockAgent(True, 100.0, 0.4), # Low wealth
            MockAgent(True, 200.0, 0.5), # Mid wealth
            MockAgent(True, 300.0, 0.6), # High wealth
            MockAgent(False, 1000.0, 0.9) # Inactive
        ]

        inequality_tracker = MockInequalityTracker()

        context = {
            "tracker": self.tracker,
            "government": self.government,
            "time": 100,
            "households": households,
            "inequality_tracker": inequality_tracker
        }

        # Act
        dto = self.system.generate_government_sensory_dto(context)

        # Assert
        self.assertEqual(dto.tick, 100)
        self.assertEqual(dto.gini_index, 0.3)

        # 3 active households.
        # Low: Bottom 50% -> 1 household (int(3*0.5)=1) -> wealth 100 -> approval 0.4
        # High: Top 20% -> 1 household (int(3*0.2)=0). Wait, int(0.6) = 0.
        # Let's recheck logic: n_high = int(n * 0.2). If n=3, n_high=0.
        # If n_high=0, approval_high_asset = 0.5 (default init)

        self.assertEqual(dto.approval_low_asset, 0.4)
        self.assertEqual(dto.approval_high_asset, 0.5)

    def test_logic_with_more_agents(self):
        # 10 agents
        households = [MockAgent(True, i*100, i/10.0) for i in range(10)]
        # wealths: 0, 100, ..., 900
        # approvals: 0.0, 0.1, ..., 0.9

        context = {
            "tracker": self.tracker,
            "government": self.government,
            "time": 100,
            "households": households,
            "inequality_tracker": MockInequalityTracker()
        }

        dto = self.system.generate_government_sensory_dto(context)

        # Bottom 50% = 5 agents (0..4). Approvals sum: 0+0.1+0.2+0.3+0.4 = 1.0. Avg = 1.0/5 = 0.2
        self.assertAlmostEqual(dto.approval_low_asset, 0.2)

        # Top 20% = 2 agents (8, 9). Approvals sum: 0.8+0.9 = 1.7. Avg = 1.7/2 = 0.85
        self.assertAlmostEqual(dto.approval_high_asset, 0.85)

if __name__ == '__main__':
    unittest.main()
