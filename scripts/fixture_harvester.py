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
    from simulation.utils.golden_loader import GoldenLoader
    fixtures = GoldenLoader.load("tests/goldens/agents_tick_100.json")
    households = fixtures.create_household_mocks()  # Type-safe mocks!
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Use the centralized GoldenLoader
from simulation.utils.golden_loader import GoldenLoader

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


# Convenience function for quick harvesting during debug
def quick_harvest(sim, tick: int, output_dir: str = "tests/goldens"):
    """
    Quick one-liner to harvest fixtures from a running simulation.
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
