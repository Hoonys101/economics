import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
from modules.household.services import HouseholdSnapshotAssembler
from simulation.ai.api import Personality
from simulation.models import Talent

class TestHouseholdSnapshotAssembler:

    @pytest.fixture
    def mock_household(self):
        # Create a mock Household with mocked internal states
        household = MagicMock(spec=Household)
        household.id = 123

        # Mock Bio State
        bio_state = BioStateDTO(
            id=123, age=30, gender="F", generation=1, is_active=True, needs={"survival": 50},
            children_ids=[1, 2]
        )
        household._bio_state = bio_state
        household.get_bio_state.return_value = bio_state

        # Mock Econ State
        econ_state = EconStateDTO(
            assets=1000.0, inventory={"food": 10}, inventory_quality={}, durable_assets=[],
            portfolio=MagicMock(), is_employed=True, employer_id=5, current_wage=100, wage_modifier=1.0,
            labor_skill=0.8, education_xp=100, education_level=2, expected_wage=110, talent=Talent(1.0, 1.0, 1.0),
            skills={}, aptitude=0.5, owned_properties=[], residing_property_id=None, is_homeless=False,
            home_quality_score=1.0, housing_target_mode="RENT", housing_price_history=[], market_wage_history=[],
            shadow_reservation_wage=90, last_labor_offer_tick=0, last_fired_tick=-1, job_search_patience=10,
            employment_start_tick=0, current_consumption=10, current_food_consumption=5, expected_inflation={},
            perceived_avg_prices={}, price_history={}, price_memory_length=10, adaptation_rate=0.1,
            labor_income_this_tick=0, capital_income_this_tick=0
        )
        household._econ_state = econ_state
        household.get_econ_state.return_value = econ_state

        # Mock Social State
        social_state = SocialStateDTO(
            personality=Personality.CONSERVATIVE, social_status=0.5, discontent=0.1, approval_rating=50,
            conformity=0.5, social_rank=0.5, quality_preference=0.5, brand_loyalty={}, last_purchase_memory={},
            patience=0.5, optimism=0.5, ambition=0.5, last_leisure_type="IDLE"
        )
        household._social_state = social_state
        household.get_social_state.return_value = social_state

        return household

    def test_assemble_snapshot_copies_state(self, mock_household):
        """Verify that the assembler creates a snapshot with deep copies of the state."""
        snapshot = HouseholdSnapshotAssembler.assemble(mock_household)

        # Verify IDs match
        assert snapshot.id == 123
        assert snapshot.bio_state.id == 123

        # Verify Content Matches
        assert snapshot.bio_state.age == 30
        assert snapshot.econ_state.assets == 1000.0
        assert snapshot.social_state.personality == Personality.CONSERVATIVE

        # Verify Independence (Copy Check)
        # Modify the original household state
        mock_household._bio_state.age = 31
        mock_household._econ_state.assets = 2000.0
        mock_household._bio_state.children_ids.append(3)

        # Snapshot should remain unchanged
        assert snapshot.bio_state.age == 30
        assert snapshot.econ_state.assets == 1000.0
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
