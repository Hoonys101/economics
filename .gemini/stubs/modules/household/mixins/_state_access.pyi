from _typeshed import Incomplete
from modules.household.dtos import BioStateDTO as BioStateDTO, EconStateDTO as EconStateDTO, HouseholdSnapshotDTO as HouseholdSnapshotDTO, HouseholdStateDTO as HouseholdStateDTO, SocialStateDTO as SocialStateDTO
from modules.household.services import HouseholdSnapshotAssembler as HouseholdSnapshotAssembler
from modules.market.loan_api import calculate_monthly_income as calculate_monthly_income, calculate_total_monthly_debt_payments as calculate_total_monthly_debt_payments
from modules.simulation.dtos.api import HouseholdConfigDTO as HouseholdConfigDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Any

logger: Incomplete

class HouseholdStateAccessMixin:
    """
    Mixin for accessing Household state.
    Provides methods to create DTOs and snapshots.
    """
    id: int
    config: HouseholdConfigDTO
    preference_asset: float
    preference_social: float
    preference_growth: float
    risk_aversion: float
    def get_bio_state(self) -> BioStateDTO:
        """Returns the biological state DTO."""
    def get_econ_state(self) -> EconStateDTO:
        """Returns the economic state DTO."""
    def get_social_state(self) -> SocialStateDTO:
        """Returns the social state DTO."""
    def create_snapshot_dto(self) -> HouseholdSnapshotDTO:
        """
        Creates a structured snapshot of the household's current state.
        Uses HouseholdSnapshotAssembler to ensure deep copies of component states.
        """
    def create_state_dto(self) -> HouseholdStateDTO:
        """
        [DEPRECATED] Use create_snapshot_dto instead.
        Creates a comprehensive DTO of the household's current state (Adapter).
        """
    def get_agent_data(self) -> dict[str, Any]:
        """Adapter for AI learning data."""
