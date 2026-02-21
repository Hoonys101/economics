import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import Set, Dict, Optional, Any
import pytest

from simulation.systems.housing_system import HousingSystem
from simulation.agents.government import Government
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.finance.api import IFinancialAgent, IBank, ISettlementSystem
from modules.common.interfaces import IResident, IPropertyOwner

# Define Protocol-compliant Mock Agent
@dataclass
class MockAgent:
    id: int
    balance_pennies: int = 1000
    owned_properties: Set[int] = field(default_factory=set)
    residing_property_id: Optional[int] = None
    is_homeless: bool = False
    is_active: bool = True

    # IFinancialAgent
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.balance_pennies

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return {DEFAULT_CURRENCY: self.balance_pennies}

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.balance_pennies += amount

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if self.balance_pennies < amount:
            raise Exception("Insufficient funds")
        self.balance_pennies -= amount

    def get_total_debt(self) -> float: return 0.0
    def get_liquid_assets(self, currency="USD") -> float: return float(self.balance_pennies)
    @property
    def total_wealth(self) -> int: return self.balance_pennies

    # IPropertyOwner
    def add_property(self, property_id: int) -> None:
        self.owned_properties.add(property_id)

    def remove_property(self, property_id: int) -> None:
        self.owned_properties.discard(property_id)

class TestHousingSystemRefactor(unittest.TestCase):

    def setUp(self):
        self.config_mock = MagicMock()
        self.config_mock.MAINTENANCE_RATE_PER_TICK = 0.01
        self.config_mock.HOMELESS_PENALTY_PER_TICK = 1.0
        self.config_mock.MORTGAGE_LTV_RATIO = 0.8
        self.config_mock.MORTGAGE_TERM_TICKS = 300
        self.config_mock.MORTGAGE_INTEREST_RATE = 0.05
        self.config_mock.FORECLOSURE_FIRE_SALE_DISCOUNT = 0.8

        self.housing_system = HousingSystem(self.config_mock)

        # Setup Simulation Mock
        self.simulation = MagicMock()
        self.simulation.time = 100
        self.simulation.settlement_system = MagicMock(spec=ISettlementSystem)
        self.simulation.bank = MagicMock(spec=IBank)
        self.simulation.government = MockAgent(id=999, balance_pennies=0) # Government is an Agent

        # Setup Agents using Protocol-compliant MockAgent
        self.tenant = MockAgent(id=1, balance_pennies=1000)
        self.tenant.residing_property_id = 101 # Set specific property

        self.owner = MockAgent(id=2, balance_pennies=5000)
        self.owner.owned_properties = {101}

        self.simulation.agents = MagicMock()
        self.simulation.agents.get.side_effect = lambda x: {
            1: self.tenant,
            2: self.owner,
            999: self.simulation.government,
            "GOVERNMENT": self.simulation.government
        }.get(x)

        self.simulation.government = self.simulation.agents.get(999)

        # Setup Units
        self.unit = MagicMock()
        self.unit.id = 101
        self.unit.owner_id = 2
        self.unit.occupant_id = 1
        self.unit.estimated_value = 10000.0
        self.unit.rent_price = 500.0
        self.unit.mortgage_id = None
        self.unit.liens = []

        self.simulation.real_estate_units = [self.unit]

    def test_process_housing_rent_collection_uses_transfer(self):
        """Test that rent collection uses SettlementSystem.transfer"""
        # Arrange
        self.unit.owner_id = 2
        self.unit.occupant_id = 1

        # Act
        self.housing_system.process_housing(self.simulation)

        # Assert
        # Verify transfer was called for rent
        self.simulation.settlement_system.transfer.assert_any_call(
            self.tenant, self.owner, 500, "rent_payment", tick=100, currency=DEFAULT_CURRENCY
        )

    def test_process_housing_maintenance_uses_transfer(self):
        """Test that maintenance cost uses SettlementSystem.transfer"""
        # Arrange
        cost = int(10000.0 * 0.01) # 100

        # Act
        self.housing_system.process_housing(self.simulation)

        # Assert
        self.simulation.settlement_system.transfer.assert_any_call(
            self.owner, self.simulation.government, cost, "housing_maintenance", tick=100, currency=DEFAULT_CURRENCY
        )
