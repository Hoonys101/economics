import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
from modules.household.services import HouseholdSnapshotAssembler
from simulation.ai.api import Personality
from simulation.models import Talent
from tests.utils.factories import create_household

class TestHouseholdSnapshotAssembler:

    @pytest.fixture
    def mock_household(self):
        household = create_household(
            id=123,
            initial_age=30,
            gender="F",
            generation=1,
            initial_needs={"survival": 50},
            assets=100000,
            personality=Personality.CONSERVATIVE,
        )
        # Customize state for specific test requirements
        household._bio_state.children_ids = [1, 2]

        household._econ_state.inventory = {"food": 10}
        household._econ_state.is_employed = True
        household._econ_state.employer_id = 5
        household._econ_state.current_wage_pennies = 10000
        # ... other econ state overrides if needed for specific assertions

        return household

    def test_assemble_snapshot_copies_state(self, mock_household):
        """Verify that the assembler creates a snapshot with deep copies of the state."""
        snapshot = HouseholdSnapshotAssembler.assemble(mock_household)

        # Verify IDs match
        assert snapshot.id == 123
        assert snapshot.bio_state.id == 123

        # Verify Content Matches
        assert snapshot.bio_state.age == 30
        from modules.system.api import DEFAULT_CURRENCY
        assert snapshot.econ_state.wallet.get_balance(DEFAULT_CURRENCY) == 100000
        assert snapshot.social_state.personality == Personality.CONSERVATIVE

        # Verify Independence (Copy Check)
        # Modify the original household state
        mock_household._bio_state.age = 31
        mock_household._deposit(100000) # 1000 + 1000 = 2000 (represented as pennies)
        mock_household._bio_state.children_ids.append(3)

        # Snapshot should remain unchanged
        assert snapshot.bio_state.age == 30
        assert snapshot.econ_state.wallet.get_balance(DEFAULT_CURRENCY) == 100000
        assert len(snapshot.bio_state.children_ids) == 2

    def test_assemble_nested_structures(self, mock_household):
        """Verify complex nested structures like inventory and needs are copied."""
        snapshot = HouseholdSnapshotAssembler.assemble(mock_household)

        # Modify nested dict in original
        mock_household._bio_state.needs["survival"] = 0
        mock_household._econ_state.inventory["food"] = 0

        # Snapshot should persist
        assert snapshot.bio_state.needs["survival"] == 50
        assert snapshot.econ_state.inventory["food"] == 10
