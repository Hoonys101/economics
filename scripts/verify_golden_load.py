import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from simulation.utils.golden_loader import GoldenLoader

def verify_golden_load():
    print("🧪 Verifying Golden Fixture Loading...")

    fixture_path = Path("tests/goldens/stable_economy.json")
    if not fixture_path.exists():
        print(f"❌ Fixture not found: {fixture_path}")
        sys.exit(1)

    try:
        # 1. Load JSON data
        data = GoldenLoader.load_json(str(fixture_path))
        print(f"✅ Loaded fixture from {fixture_path}")

        households_data = data.get("households", [])
        if not households_data:
            print("❌ No households found in fixture data!")
            sys.exit(1)

        print(f"✅ Found {len(households_data)} households in fixture.")

        # 2. Convert to Mocks
        # We simulate what create_household_mocks does
        mock_households = [GoldenLoader.dict_to_mock(h) for h in households_data]

        first_household = mock_households[0]

        print(f"✅ First household type: {type(first_household)}")
        if not isinstance(first_household, MagicMock):
             print(f"⚠️ Warning: Expected MagicMock, got {type(first_household)}.")

        # Verify attributes
        if hasattr(first_household, 'id'):
             print(f"✅ household.id: {first_household.id}")
        else:
             print("❌ household.id missing")

        val_age = getattr(first_household, 'age', None)
        print(f"✅ household._bio_state.age (direct): {val_age}")

        if val_age is None:
             print("❌ household._bio_state.age is missing!")
             sys.exit(1)

        print("✅ Verification Successful")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_golden_load()
