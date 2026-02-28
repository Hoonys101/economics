import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any

from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.housing_system import HousingSystem
from simulation.models import RealEstateUnit
from modules.finance.api import IFinancialAgent, IBank, IFinancialEntity, LienDTO, ICentralBank
from modules.common.interfaces import IPropertyOwner, IResident
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode

@dataclass
class MockAgent:
    id: int
    balance_pennies: int = 1000
    owned_properties: Set[int] = field(default_factory=set)
    residing_property_id: Optional[int] = None
    is_homeless: bool = False

    # IFinancialAgent Protocol Implementation
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.balance_pennies

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return {DEFAULT_CURRENCY: self.balance_pennies}

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.balance_pennies += amount

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._deposit(amount, currency)

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if self.balance_pennies < amount:
            raise Exception("Insufficient funds") # SettlementSystem should check this first
        self.balance_pennies -= amount

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._withdraw(amount, currency)

    def get_total_debt(self) -> float:
        return 0.0

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> float:
        return float(self.balance_pennies)

    @property
    def total_wealth(self) -> int:
        return self.balance_pennies

    # IPropertyOwner Implementation
    def add_property(self, property_id: int) -> None:
        self.owned_properties.add(property_id)

    def remove_property(self, property_id: int) -> None:
        self.owned_properties.discard(property_id)

@dataclass
class MockCentralBank:
    id: int = 0
    base_rate: float = 0.05
    balance_pennies: int = 0

    # ICentralBank Protocol Implementation
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return 999999999999 # Infinite for testing

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return {DEFAULT_CURRENCY: self.get_balance()}

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        pass

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        pass

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        pass

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        pass

    def get_total_debt(self) -> float:
        return 0.0

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> float:
        return float(self.get_balance())

    @property
    def total_wealth(self) -> int:
        return self.get_balance()

    def process_omo_settlement(self, transaction: Any) -> None:
        pass

    def execute_open_market_operation(self, instruction: Any) -> List[Any]:
        return []

    def check_and_provide_liquidity(self, bank_agent: Any, amount_needed: int) -> Optional[Any]:
        return None

class TestProtocolIntegrity:

    @pytest.fixture
    def settlement_system(self):
        return SettlementSystem()

    def test_settlement_overdraft_protection(self, settlement_system):
        """Test that SettlementSystem prevents transfers if sender has insufficient funds."""
        sender = MockAgent(id=1, balance_pennies=100)
        receiver = MockAgent(id=2, balance_pennies=0)

        # Attempt to transfer 150 (more than balance)
        tx = settlement_system.transfer(sender, receiver, 150, "overdraft_test")

        assert tx is None
        assert sender.balance_pennies == 100
        assert receiver.balance_pennies == 0

    def test_settlement_zero_sum(self, settlement_system):
        """Test that successful transfer is zero-sum."""
        sender = MockAgent(id=1, balance_pennies=100)
        receiver = MockAgent(id=2, balance_pennies=0)

        initial_sum = sender.balance_pennies + receiver.balance_pennies

        tx = settlement_system.transfer(sender, receiver, 50, "transfer_test")

        assert tx is not None
        assert sender.balance_pennies == 50
        assert receiver.balance_pennies == 50

        final_sum = sender.balance_pennies + receiver.balance_pennies
        assert initial_sum == final_sum

    def test_central_bank_infinite_funds(self, settlement_system):
        """Test that Central Bank can transfer without explicit funds check (Mock implementation)."""
        cb = MockCentralBank(id=0)
        receiver = MockAgent(id=2, balance_pennies=0)

        # CB transfers money
        # Note: SettlementSystem checks isinstance(agent, ICentralBank) to bypass funds check
        tx = settlement_system.transfer(cb, receiver, 1000, "cb_transfer")

        assert tx is not None
        assert receiver.balance_pennies == 1000

    def test_real_estate_unit_lien_dto(self):
        """Test RealEstateUnit works with LienDTO."""
        unit = RealEstateUnit(id=1, owner_id=1, estimated_value=10000)

        lien = LienDTO(
            loan_id="loan_123",
            lienholder_id=2,
            principal_remaining=5000,
            lien_type="MORTGAGE"
        )

        unit.liens.append(lien)

        # Test property access
        assert unit.mortgage_id == "loan_123"

        # Test with legacy dict (Backwards Compatibility)
        unit.liens = [{
            "loan_id": "loan_456",
            "lienholder_id": 2,
            "principal_remaining": 5000,
            "lien_type": "MORTGAGE"
        }]

        assert unit.mortgage_id == "loan_456"

    def test_housing_system_maintenance_zero_sum(self, settlement_system):
        """Test that housing maintenance payments are zero-sum via SettlementSystem."""
        # Use simple mock for config
        class MockConfig:
            MAINTENANCE_RATE_PER_TICK = 0.01

        housing_config = MockConfig()

        housing_system = HousingSystem(housing_config)

        owner = MockAgent(id=1, balance_pennies=10000)
        gov = MockAgent(id=99, balance_pennies=0)

        unit = RealEstateUnit(id=1, owner_id=1, estimated_value=10000, rent_price=100)

        simulation = MagicMock()
        simulation.real_estate_units = [unit]
        # Use MagicMock for agents dict behavior
        agents_mock = MagicMock()
        agents_mock.get.side_effect = lambda id: {1: owner, 99: gov}.get(id)
        simulation.agents = agents_mock

        simulation.settlement_system = settlement_system
        simulation.government = gov
        simulation.time = 1

        # Initial State
        initial_total = owner.balance_pennies + gov.balance_pennies

        # Run process
        housing_system.process_housing(simulation)

        # Expected Cost: 10000 * 0.01 = 100
        expected_cost = 100

        assert owner.balance_pennies == 10000 - expected_cost
        assert gov.balance_pennies == expected_cost
        assert owner.balance_pennies + gov.balance_pennies == initial_total

    def test_housing_system_rent_zero_sum(self, settlement_system):
        """Test that rent payments are zero-sum."""
        class MockConfig:
            MAINTENANCE_RATE_PER_TICK = 0.0 # Disable maintenance to isolate rent

        housing_config = MockConfig()

        housing_system = HousingSystem(housing_config)

        landlord = MockAgent(id=1, balance_pennies=0)
        tenant = MockAgent(id=2, balance_pennies=1000, residing_property_id=1)

        unit = RealEstateUnit(id=1, owner_id=1, occupant_id=2, rent_price=500, estimated_value=10000)

        simulation = MagicMock()
        simulation.real_estate_units = [unit]

        agents_mock = MagicMock()
        agents_mock.get.side_effect = lambda id: {1: landlord, 2: tenant}.get(id)
        simulation.agents = agents_mock

        simulation.settlement_system = settlement_system
        simulation.government = MockAgent(id=99) # Gov not involved in rent
        simulation.time = 1

        initial_total = landlord.balance_pennies + tenant.balance_pennies

        housing_system.process_housing(simulation)

        assert tenant.balance_pennies == 500
        assert landlord.balance_pennies == 500
        assert landlord.balance_pennies + tenant.balance_pennies == initial_total
