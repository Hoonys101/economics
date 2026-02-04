
import sys
import os
import unittest
from unittest.mock import MagicMock

# Adjust path to allow imports
sys.path.append(os.getcwd())

from simulation.agents.central_bank import CentralBank
from simulation.agents.government import Government
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import DEFAULT_CURRENCY
from simulation.ai.enums import EconomicSchool, PolicyActionTag

class TestReproTD(unittest.TestCase):
    def test_central_bank_id_mismatch(self):
        # Mock dependencies
        tracker = MagicMock()
        config = MagicMock()
        # Mock float values for formatting
        config.INITIAL_BASE_ANNUAL_RATE = 0.05
        config.CB_INFLATION_TARGET = 0.02

        cb = CentralBank(tracker, config)

        # Refactor Verified: ID is int and matches wallet
        self.assertIsInstance(cb.id, int)
        self.assertEqual(cb.id, 0)
        self.assertIsInstance(cb.wallet.owner_id, int)
        self.assertEqual(cb.wallet.owner_id, cb.id)

    def test_settlement_system_check(self):
        ss = SettlementSystem()
        cb = MagicMock()
        cb.id = "CENTRAL_BANK"
        cb.__class__.__name__ = "CentralBank"
        pass

    def test_government_fire_advisor(self):
        config = MagicMock()
        gov = Government(id=1, initial_assets=1000, config_module=config)
        gov.policy_lockout_manager = MagicMock()

        # Test refactored implementation
        gov.fire_advisor(EconomicSchool.KEYNESIAN, 0)
        gov.policy_lockout_manager.lock_policy.assert_called_with(PolicyActionTag.KEYNESIAN_FISCAL, 20, 0)

        # Verify map existence
        self.assertTrue(hasattr(gov, "SCHOOL_TO_POLICY_MAP"))
        self.assertIn(EconomicSchool.KEYNESIAN, gov.SCHOOL_TO_POLICY_MAP)

if __name__ == '__main__':
    unittest.main()
