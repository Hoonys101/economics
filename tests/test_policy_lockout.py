import unittest
from unittest.mock import MagicMock
from simulation.ai.enums import EconomicSchool, PolicyActionTag
from modules.government.components.policy_lockout_manager import PolicyLockoutManager
from simulation.agents.government import Government

class TestPolicyLockout(unittest.TestCase):
    def test_manager_lockout(self):
        manager = PolicyLockoutManager()
        tag = PolicyActionTag.KEYNESIAN_FISCAL
        current_tick = 100
        duration = 20

        # Initial check
        self.assertFalse(manager.is_locked(tag, current_tick))

        # Lock
        manager.lock_policy(tag, duration, current_tick)

        # Check during lockout (100 to 119)
        self.assertTrue(manager.is_locked(tag, 100))
        self.assertTrue(manager.is_locked(tag, 110))
        self.assertTrue(manager.is_locked(tag, 119))

        # Check after lockout (120)
        self.assertFalse(manager.is_locked(tag, 120))

        # Extend lock
        manager.lock_policy(tag, 30, 100) # Ends at 130
        self.assertTrue(manager.is_locked(tag, 125))
        self.assertFalse(manager.is_locked(tag, 130))

    def test_government_fire_advisor(self):
        # Mock dependencies
        config_mock = MagicMock()
        config_mock.TICKS_PER_YEAR = 360
        config_mock.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        config_mock.INCOME_TAX_RATE = 0.1
        config_mock.CORPORATE_TAX_RATE = 0.2
        config_mock.TAX_MODE = "PROGRESSIVE"

        # Instantiate Government
        gov = Government(id=1, initial_assets=1000.0, config_module=config_mock)

        # Ensure manager is initialized
        self.assertIsInstance(gov.policy_lockout_manager, PolicyLockoutManager)

        # Fire advisor
        current_tick = 500
        gov.fire_advisor(EconomicSchool.KEYNESIAN, current_tick)

        # Verify lockout
        self.assertTrue(gov.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, 500))
        self.assertTrue(gov.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, 519))
        self.assertFalse(gov.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, 520))

        # Verify other tags are NOT locked
        self.assertFalse(gov.policy_lockout_manager.is_locked(PolicyActionTag.AUSTRIAN_AUSTERITY, 500))

if __name__ == '__main__':
    unittest.main()
