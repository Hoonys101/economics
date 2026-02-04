from __future__ import annotations
from typing import Protocol, List
from simulation.ai.enums import PoliticalParty
from modules.government.dtos import PolicyActionDTO
from simulation.dtos import GovernmentStateDTO as SensoryDTO

class IAdaptiveGovBrain(Protocol):
    """
    Interface for the utility-driven political decision engine.
    """

    def propose_actions(self, sensory_data: SensoryDTO, ruling_party: PoliticalParty) -> List[PolicyActionDTO]:
        """
        Generates and scores a list of potential policy actions based on the
        current state and ruling party's ideology.

        Args:
            sensory_data: A snapshot of the current socio-economic state.
            ruling_party: The political party currently in power.

        Returns:
            A list of PolicyActionDTOs, sorted by calculated utility in descending order.
        """
        ...
