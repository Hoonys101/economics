"""
Fixture Harvester: Auto-Mock Generation via Golden Sample Recording

This module provides utilities to:
1. Capture real agent states during simulation runs
2. Serialize them to JSON "Golden Fixtures"  
3. Load them in tests to create type-safe mock objects

Usage:
    # During a real simulation run (e.g., in a debug script)
    from scripts.fixture_harvester import FixtureHarvester
    harvester = FixtureHarvester(output_dir="tests/goldens")
    harvester.capture_agents(sim.households, sim.firms, tick=100)
    harvester.save_all()

    # In a test (conftest.py or test file)
    from scripts.fixture_harvester import GoldenLoader
    fixtures = GoldenLoader.load("tests/goldens/agents_tick_100.json")
    households = fixtures.create_household_mocks()  # Type-safe mocks!
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

# Attempt to import the new generic loader
try:
    from tests.utils.golden_loader import GoldenLoader as GenericGoldenLoader
except ImportError:
    # If not in path (e.g. running script directly from shell), try adding root
    sys.path.append(os.getcwd())
    try:
        from tests.utils.golden_loader import GoldenLoader as GenericGoldenLoader
    except ImportError:
        # Fallback if tests/utils/golden_loader.py is missing or unreachable
        GenericGoldenLoader = None


@dataclass
class HouseholdSnapshot:
    """Serializable representation of a Household agent."""
    id: int
    assets: float
    is_active: bool
    is_employed: bool
    employer_id: Optional[int]
    age: int
    education_level: float
    current_wage: float
    needs: Dict[str, float]
    inventory: Dict[str, float]
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
    inventory: Dict[str, float]
    retained_earnings: float
    total_debt: float
    current_profit: float
    consecutive_loss_turns: int


@dataclass
class GoldenFixture:
    """Complete fixture containing agent snapshots."""
    metadata: Dict[str, Any]
    households: List[HouseholdSnapshot]
    firms: List[FirmSnapshot]
    config_snapshot: Dict[str, Any]


class FixtureHarvester:
    """
    Captures real agent states during simulation runs for test fixtures.
    
    Example:
        harvester = FixtureHarvester(output_dir="tests/goldens")
        harvester.capture_agents(sim.households, sim.firms, tick=100)
        harvester.capture_config(sim.config_module)
        harvester.save_all()
    """
    
    def __init__(self, output_dir: str = "tests/goldens"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.households: List[HouseholdSnapshot] = []
        self.firms: List[FirmSnapshot] = []
        self.config_snapshot: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {
            "captured_at": datetime.now().isoformat(),
            "tick": 0
        }
    
    def capture_household(self, household) -> HouseholdSnapshot:
        """Capture a single household's state."""
        return HouseholdSnapshot(
            id=household.id,
            assets=getattr(household, 'assets', 0.0),
            is_active=getattr(household, 'is_active', True),
            is_employed=getattr(household, 'is_employed', False),
            employer_id=getattr(household, 'employer_id', None),
            age=getattr(household, 'age', 0),
            education_level=getattr(household, 'education_level', 1.0),
            current_wage=getattr(household, 'current_wage', 0.0),
            needs=dict(getattr(household, 'needs', {})),
            inventory=dict(getattr(household, 'inventory', {})),
            approval_rating=getattr(household, 'approval_rating', 1.0)
        )
    
    def capture_firm(self, firm) -> FirmSnapshot:
        """Capture a single firm's state."""
        employees = getattr(firm, 'employees', [])
        employees_count = len(employees) if hasattr(employees, '__len__') else 0
        
        return FirmSnapshot(
            id=firm.id,
            assets=getattr(firm, 'assets', 0.0),
            is_active=getattr(firm, 'is_active', True),
            specialization=getattr(firm, 'specialization', 'food'),
            productivity_factor=getattr(firm, 'productivity_factor', 1.0),
            employees_count=employees_count,
            inventory=dict(getattr(firm, 'inventory', {})),
            retained_earnings=getattr(firm, 'retained_earnings', 0.0),
            total_debt=getattr(firm, 'total_debt', 0.0),
            current_profit=getattr(firm, 'current_profit', 0.0),
            consecutive_loss_turns=getattr(firm, 'consecutive_loss_turns', 0)
        )
    
    def capture_agents(self, households: List, firms: List, tick: int = 0):
        """Capture all agents' states at a given tick."""
        self.metadata["tick"] = tick
        self.metadata["household_count"] = len(households)
        self.metadata["firm_count"] = len(firms)
        
        self.households = [self.capture_household(h) for h in households]
        self.firms = [self.capture_firm(f) for f in firms]
        
        print(f"📸 Captured {len(self.households)} households and {len(self.firms)} firms at tick {tick}")
    
    def capture_config(self, config_module):
        """Capture relevant config values."""
        # Extract scalar values from config module
        for attr in dir(config_module):
            if attr.isupper():  # Only capture uppercase constants
                # Filter out sensitive keys
                if "TOKEN" in attr or "SECRET" in attr or "KEY" in attr or "PASSWORD" in attr:
                    continue

                value = getattr(config_module, attr)
                if isinstance(value, (int, float, str, bool, list, dict)):
                    self.config_snapshot[attr] = value
    
    def save_all(self, filename: Optional[str] = None) -> Path:
        """Save all captured data to a JSON file."""
        if filename is None:
            filename = f"agents_tick_{self.metadata.get('tick', 0)}.json"
        
        filepath = self.output_dir / filename
        
        fixture = GoldenFixture(
            metadata=self.metadata,
            households=self.households,
            firms=self.firms,
            config_snapshot=self.config_snapshot
        )
        
        # Convert dataclasses to dicts for JSON serialization
        data = {
            "metadata": fixture.metadata,
            "households": [asdict(h) for h in fixture.households],
            "firms": [asdict(f) for f in fixture.firms],
            "config_snapshot": fixture.config_snapshot
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved golden fixture to: {filepath}")
        return filepath


class GoldenLoader:
    """
    Loads golden fixtures and creates type-safe mock objects.
    
    Example:
        fixtures = GoldenLoader.load("tests/goldens/agents_tick_100.json")
        households = fixtures.create_household_mocks()
        firms = fixtures.create_firm_mocks()
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.metadata = data.get("metadata", {})
        self.households_data = data.get("households", [])
        self.firms_data = data.get("firms", [])
        self.config_snapshot = data.get("config_snapshot", {})
    
    @classmethod
    def load(cls, filepath: str) -> "GoldenLoader":
        """Load a golden fixture from file."""
        if GenericGoldenLoader:
            data = GenericGoldenLoader.load_json(filepath)
        else:
             with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return cls(data)
    
    def create_household_mocks(self, mock_class=None):
        """
        Create mock households from golden data.
        
        Args:
            mock_class: Optional - The actual Household class to use.
                       If None, creates SimpleNamespace objects (legacy behavior) or MagicMock if generic loader used.
        """
        mocks = []
        for h_data in self.households_data:
            if GenericGoldenLoader:
                # Use GenericGoldenLoader to do the basic conversion
                mock = GenericGoldenLoader.dict_to_mock(h_data, spec=mock_class)
            else:
                # Fallback to old logic
                from types import SimpleNamespace
                if mock_class:
                    mock = MagicMock(spec=mock_class)
                else:
                    mock = SimpleNamespace()
                for key, value in h_data.items():
                    setattr(mock, key, value)

            # Add standard mock methods
            # logic methods are never in data, so we can safely set them
            mock.make_decision = MagicMock(return_value=([], MagicMock()))

            # Ensure complex nested mocks exist
            # (Explicitly setting them ensures they exist even if we use SimpleNamespace in fallback)
            if not hasattr(mock, 'decision_engine'):
                mock.decision_engine = MagicMock()
            if not hasattr(mock.decision_engine, 'ai_engine'):
                mock.decision_engine.ai_engine = MagicMock()
            
            mocks.append(mock)
        
        return mocks
    
    def create_firm_mocks(self, mock_class=None):
        """
        Create mock firms from golden data.
        
        Args:
            mock_class: Optional - The actual Firm class to use.
                       If None, creates SimpleNamespace objects (legacy behavior) or MagicMock if generic loader used.
        """
        mocks = []
        for f_data in self.firms_data:
            if GenericGoldenLoader:
                mock = GenericGoldenLoader.dict_to_mock(f_data, spec=mock_class)
            else:
                from types import SimpleNamespace
                if mock_class:
                    mock = MagicMock(spec=mock_class)
                else:
                    mock = SimpleNamespace()
                for key, value in f_data.items():
                    setattr(mock, key, value)
            
            # Add required mock methods
            mock.make_decision = MagicMock(return_value=([], MagicMock()))

            if not hasattr(mock, 'decision_engine'):
                mock.decision_engine = MagicMock()
            if not hasattr(mock.decision_engine, 'ai_engine'):
                mock.decision_engine.ai_engine = MagicMock()

            # HR logic
            if not hasattr(mock, 'hr'):
                mock.hr = MagicMock()

            # If employees wasn't in data (it's not in snapshot, only count is), ensure it's empty list
            # We must force this because MagicMock would return a Mock object for 'employees' otherwise
            mock.hr.employees = []
            
            # Add get_financial_snapshot based on captured data
            # Logic method, always mock it
            mock.get_financial_snapshot = MagicMock(return_value={
                "total_assets": f_data.get("assets", 0) + sum(f_data.get("inventory", {}).values()) * 10,
                "working_capital": f_data.get("assets", 0),
                "retained_earnings": f_data.get("retained_earnings", 0),
                "average_profit": f_data.get("current_profit", 0),
                "total_debt": f_data.get("total_debt", 0)
            })
            
            mocks.append(mock)
        
        return mocks
    
    def create_config_mock(self):
        """Create a mock config module from golden data."""
        if GenericGoldenLoader:
            return GenericGoldenLoader.dict_to_mock(self.config_snapshot)
        else:
            from types import SimpleNamespace
            mock = SimpleNamespace()
            for key, value in self.config_snapshot.items():
                setattr(mock, key, value)
            return mock


# Convenience function for quick harvesting during debug
def quick_harvest(sim, tick: int, output_dir: str = "tests/goldens"):
    """
    Quick one-liner to harvest fixtures from a running simulation.
    
    Usage (in debug script or notebook):
        from scripts.fixture_harvester import quick_harvest
        quick_harvest(sim, tick=100)
    """
    harvester = FixtureHarvester(output_dir=output_dir)
    harvester.capture_agents(sim.households, sim.firms, tick)
    harvester.capture_config(sim.config_module)
    return harvester.save_all()


if __name__ == "__main__":
    # Demo: Create a sample golden fixture
    print("🧪 Fixture Harvester Demo")
    print("=" * 50)
    
    # Create dummy data for demonstration
    class DummyHousehold:
        def __init__(self, id):
            self.id = id
            self.assets = 1000.0 + id * 100
            self.is_active = True
            self.is_employed = id % 2 == 0
            self.employer_id = 100 if self.is_employed else None
            self.age = 25 + id
            self.education_level = 1.0
            self.current_wage = 50.0 if self.is_employed else 0.0
            self.needs = {"survival": 0.5}
            self.inventory = {}
            self.approval_rating = 0.8
    
    class DummyFirm:
        def __init__(self, id):
            self.id = id
            self.assets = 5000.0 + id * 500
            self.is_active = True
            self.specialization = "food" if id % 2 == 0 else "electronics"
            self.productivity_factor = 1.0
            self.employees = [DummyHousehold(i) for i in range(3)]
            self.inventory = {self.specialization: 10.0}
            self.retained_earnings = 500.0
            self.total_debt = 0.0
            self.current_profit = 100.0
            self.consecutive_loss_turns = 0
    
    # Harvest
    households = [DummyHousehold(i) for i in range(5)]
    firms = [DummyFirm(100 + i) for i in range(3)]
    
    harvester = FixtureHarvester(output_dir="tests/goldens")
    harvester.capture_agents(households, firms, tick=0)
    filepath = harvester.save_all("demo_fixture.json")
    
    # Load and verify
    print("\n📂 Loading saved fixture...")
    loader = GoldenLoader.load(str(filepath))
    
    mock_households = loader.create_household_mocks()
    mock_firms = loader.create_firm_mocks()
    
    print(f"✅ Created {len(mock_households)} household mocks")
    print(f"✅ Created {len(mock_firms)} firm mocks")
    print(f"\n🔍 Sample Household Mock:")
    print(f"   ID: {mock_households[0].id}")
    print(f"   Assets: {mock_households[0].assets}")
    print(f"   Employed: {mock_households[0].is_employed}")
    
    print(f"\n🔍 Sample Firm Mock:")
    print(f"   ID: {mock_firms[0].id}")
    print(f"   Assets: {mock_firms[0].assets}")
    print(f"   Specialization: {mock_firms[0].specialization}")
    print(f"   Financial Snapshot: {mock_firms[0].get_financial_snapshot()}")
