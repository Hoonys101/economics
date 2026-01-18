import unittest
from unittest.mock import MagicMock
from simulation.components.agent_lifecycle_component import AgentLifecycleComponent
from simulation.core_agents import Household

class TestAgentLifecycleComponent(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.owner = MagicMock(spec=Household)
        self.owner.id = 1
        self.owner.is_employed = True
        # Setup mocks for sub-components
        self.owner.labor_manager = MagicMock()
        self.owner.economy_manager = MagicMock()
        self.owner.psychology = MagicMock()

        self.component = AgentLifecycleComponent(self.owner, self.config)

    def test_run_tick(self):
        context = {
            "household": self.owner,
            "market_data": {},
            "time": 1
        }

        self.component.run_tick(context)

        # Verify orchestration
        self.owner.labor_manager.work.assert_called_with(8.0)
        self.owner.economy_manager.pay_taxes.assert_called()
        self.owner.psychology.update_needs.assert_called()

        # Consumption should NOT be called here (handled by CommerceSystem)
        # We don't have a consumption mock to check NOT called, but we verified the code logic.

if __name__ == '__main__':
    unittest.main()
