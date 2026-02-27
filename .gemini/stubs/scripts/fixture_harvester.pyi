from _typeshed import Incomplete
from dataclasses import dataclass
from modules.household.dtos import HouseholdStateDTO
from modules.simulation.dtos.api import FirmStateDTO
from pathlib import Path
from typing import Any

@dataclass
class HouseholdSnapshot:
    """Serializable representation of a Household agent."""
    id: int
    assets: float
    is_active: bool
    is_employed: bool
    employer_id: int | None
    age: int
    education_level: float
    current_wage: float
    needs: dict[str, float]
    inventory: dict[str, float]
    approval_rating: float

@dataclass
class FirmSnapshot:
    """Serializable representation of a Firm agent."""
    id: int
    assets: float
    is_active: bool
    specialization: str
    productivity_factor: float
    employees_count: int
    inventory: dict[str, float]
    retained_earnings: float
    total_debt: float
    current_profit: float
    consecutive_loss_turns: int

@dataclass
class GoldenFixture:
    """Complete fixture containing agent snapshots."""
    metadata: dict[str, Any]
    households: list[HouseholdSnapshot]
    firms: list[FirmSnapshot]
    config_snapshot: dict[str, Any]
    goods_data: list[dict[str, Any]] = ...
    market_data: dict[str, Any] = ...

class FixtureHarvester:
    '''
    Captures real agent states during simulation runs for test fixtures.
    
    Example:
        harvester = FixtureHarvester(output_dir="tests/goldens")
        harvester.capture_agents(sim.households, sim.firms, tick=100)
        harvester.capture_config(sim.config_module)
        harvester.capture_environment(sim.goods_data, sim.market_data)
        harvester.save_all()
    '''
    output_dir: Incomplete
    households: list[HouseholdSnapshot]
    firms: list[FirmSnapshot]
    config_snapshot: dict[str, Any]
    goods_data: list[dict[str, Any]]
    market_data: dict[str, Any]
    metadata: dict[str, Any]
    def __init__(self, output_dir: str = 'tests/goldens') -> None: ...
    def capture_household(self, household) -> HouseholdSnapshot:
        """Capture a single household's state."""
    def capture_firm(self, firm) -> FirmSnapshot:
        """Capture a single firm's state."""
    def capture_agents(self, households: list, firms: list, tick: int = 0):
        """Capture all agents' states at a given tick."""
    def capture_config(self, config_module) -> None:
        """Capture relevant config values."""
    def capture_environment(self, goods_data: list[dict[str, Any]], market_data: dict[str, Any]):
        """Capture environment data (GoodsDTO, MarketHistoryDTO)."""
    def save_all(self, filename: str | None = None) -> Path:
        """Save all captured data to a JSON file."""

class GoldenLoader:
    '''
    Loads golden fixtures and creates type-safe mock objects.
    
    Example:
        fixtures = GoldenLoader.load("tests/goldens/agents_tick_100.json")
        households = fixtures.create_household_mocks()
        firms = fixtures.create_firm_mocks()
    '''
    metadata: Incomplete
    households_data: Incomplete
    firms_data: Incomplete
    config_snapshot: Incomplete
    goods_data: Incomplete
    market_data: Incomplete
    def __init__(self, data: dict[str, Any]) -> None: ...
    @classmethod
    def load(cls, filepath: str) -> GoldenLoader:
        """Load a golden fixture from file."""
    def create_household_mocks(self, mock_class=None):
        """
        Create mock households from golden data.
        Enforces integer precision for monetary values (MIGRATION).
        """
    def create_household_dto_list(self) -> list[HouseholdStateDTO]:
        """Creates actual HouseholdStateDTO objects from golden data."""
    def create_firm_mocks(self, mock_class=None):
        """
        Create mock firms from golden data.
        Enforces integer precision for monetary values (MIGRATION).
        """
    def create_firm_dto_list(self) -> list[FirmStateDTO]:
        """Creates actual FirmStateDTO objects from golden data."""
    def create_config_mock(self):
        """Create a mock config module from golden data."""

def quick_harvest(sim, tick: int, output_dir: str = 'tests/goldens'):
    """
    Quick one-liner to harvest fixtures from a running simulation.
    
    Usage (in debug script or notebook):
        from scripts.fixture_harvester import quick_harvest
        quick_harvest(sim, tick=100)
    """
