import pytest
from tests.utils.factories import create_household
from modules.system.api import DEFAULT_CURRENCY
from simulation.core_agents import Household
from unittest.mock import MagicMock

def test_repro():
    try:
        household = create_household(
            assets=10000,
            id=1
        )
        print("Success")
    except TypeError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {e}")

if __name__ == "__main__":
    test_repro()
