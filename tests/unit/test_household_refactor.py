import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from modules.household.dtos import EconStateDTO, BioStateDTO, SocialStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.ai.api import Personality
from simulation.models import Talent
from modules.simulation.api import AgentCoreConfigDTO
from tests.utils.factories import create_household_config_dto

class TestHouseholdRefactor:
    def test_property_management(self):
        # Setup DTOs using factory for completeness
        config = create_household_config_dto()

        # Override specific values if needed by test, though defaults are usually fine
        # Here we just need it to be a valid DTO.

        core_config = AgentCoreConfigDTO(
            id=1,
            name="Household_1",
            value_orientation="neutral",
            initial_needs={},
            logger=MagicMock(),
            memory_interface=None
        )

        # Initialize Household
        household = Household(
            core_config=core_config,
            engine=MagicMock(),
            talent=Talent(base_learning_rate=0.1, max_potential=1.0),
            goods_data=[],
            personality=Personality.BALANCED,
            config_dto=config,
            initial_assets_record=1000.0
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
