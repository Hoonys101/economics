import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from modules.household.dtos import EconStateDTO, BioStateDTO, SocialStateDTO
from modules.simulation.dtos.api import HouseholdConfigDTO
from simulation.ai.api import Personality
from simulation.models import Talent
from modules.simulation.api import AgentCoreConfigDTO
from tests.utils.factories import create_household_config_dto, create_household

class TestHouseholdRefactor:
    def test_property_management(self):
        # Setup DTOs using factory for completeness
        config = create_household_config_dto()

        # Initialize Household using the specialized factory
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
        assert 101 in household.state.econ_state.owned_properties
        assert household.state.econ_state.owned_properties == [101]

        # Test add duplicate (should handle safe?)
        household.add_property(101)
        assert household.state.econ_state.owned_properties == [101]

        # Test remove_property
        household.remove_property(101)
        assert 101 not in household.state.econ_state.owned_properties
        assert household.state.econ_state.owned_properties == []

        # Test remove non-existent
        household.remove_property(999) # Should not raise error
        assert household.state.econ_state.owned_properties == []
