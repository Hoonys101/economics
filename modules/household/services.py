from typing import TYPE_CHECKING
from modules.household.dtos import HouseholdSnapshotDTO

if TYPE_CHECKING:
    from simulation.core_agents import Household

class HouseholdSnapshotAssembler:
    """
    Service responsible for assembling a complete, read-only snapshot
    of a Household agent's state from its internal components.
    """

    @staticmethod
    def assemble(household: "Household") -> HouseholdSnapshotDTO:
        """
        Creates a snapshot DTO from a household agent instance.
        Ensures internal state is copied to prevent accidental mutation.
        """
        # We assume the household components expose their state DTOs
        # and that we should copy them for the snapshot to be immutable.

        # Access internal states via public accessors (TD-217)
        bio_state_copy = household.get_bio_state().copy()
        econ_state_copy = household.get_econ_state().copy()
        social_state_copy = household.get_social_state().copy()

        return HouseholdSnapshotDTO(
            id=household.id,
            bio_state=bio_state_copy,
            econ_state=econ_state_copy,
            social_state=social_state_copy
        )
