from modules.household.dtos import HouseholdSnapshotDTO as HouseholdSnapshotDTO
from simulation.core_agents import Household as Household

class HouseholdSnapshotAssembler:
    """
    Service responsible for assembling a complete, read-only snapshot
    of a Household agent's state from its internal components.
    """
    @staticmethod
    def assemble(household: Household, monthly_income_pennies: int = 0, monthly_debt_payments_pennies: int = 0) -> HouseholdSnapshotDTO:
        """
        Creates a snapshot DTO from a household agent instance.
        Ensures internal state is copied to prevent accidental mutation.
        """
