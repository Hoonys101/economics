import unittest
from _typeshed import Incomplete
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from unittest.mock import ANY as ANY

class TestEconomicIntegrityAudit(unittest.TestCase):
    config: Incomplete
    logger: Incomplete
    settlement_system: Incomplete
    taxation_system: Incomplete
    government: Incomplete
    def setUp(self) -> None: ...
    def test_birth_gift_rounding(self, mock_create_config, mock_household_cls, mock_household_factory_cls) -> None:
        """
        Verify that birth gift is calculated in pennies (integer).
        """
    def test_inheritance_distribution(self):
        """
        Verify that inheritance distribution transfers full amount to heir (no dust sweep).
        """
    def test_public_manager_tax_atomicity(self) -> None:
        """
        Verify Public Manager sales collect tax using settle_atomic.
        """
