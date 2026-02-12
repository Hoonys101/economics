from typing import TYPE_CHECKING

if TYPE_CHECKING:
     from simulation.core_agents import Household
     from modules.household.dtos import EconStateDTO, BioStateDTO, SocialStateDTO

class HouseholdStateContainer:
    """Helper to expose Household state components."""
    def __init__(self, agent: "Household"):
        self._agent = agent

    @property
    def econ_state(self) -> "EconStateDTO":
        return self._agent._econ_state

    @property
    def bio_state(self) -> "BioStateDTO":
        return self._agent._bio_state

    @property
    def social_state(self) -> "SocialStateDTO":
        return self._agent._social_state
