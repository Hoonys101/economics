import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from modules.household.dtos import EconStateDTO, BioStateDTO, SocialStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.ai.api import Personality
from simulation.models import Talent
from tests.utils.factories import create_household

class TestHouseholdRefactor:
    def test_property_management(self):
        # Setup DTOs
        config = MagicMock(spec=HouseholdConfigDTO)
        config.value_orientation_mapping = {}
        config.initial_household_age_range = (20, 30)
        config.price_memory_length = 10
        config.wage_memory_length = 10
        config.ticks_per_year = 100
        config.initial_aptitude_distribution = (0.5, 0.1)
        config.conformity_ranges = {}
        config.initial_household_assets_mean = 1000.0
        config.quality_pref_snob_min = 0.8
        config.quality_pref_miser_max = 0.2
        config.adaptation_rate_normal = 0.1

        # Initialize Household
        household = create_household(
            config_dto=config,
            id=1,
            talent=Talent(base_learning_rate=0.1, max_potential=1.0),
            goods_data=[],
            assets=1000.0,
            initial_needs={},
            engine=MagicMock(),
            value_orientation="neutral",
            personality=Personality.BALANCED,
        )

        # Test add_property
        household.add_property(101)
        assert 101 in household.owned_properties
        assert household.owned_properties == [101]

        # Test add duplicate (should handle safe?)
        # Implementation: if property_id not in ... append
        household.add_property(101)
        assert household.owned_properties == [101]

        # Test remove_property
        household.remove_property(101)
        assert 101 not in household.owned_properties
        assert household.owned_properties == []

        # Test remove non-existent
        household.remove_property(999) # Should not raise error
        assert household.owned_properties == []
