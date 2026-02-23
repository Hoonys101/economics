from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
import copy
import logging

from modules.system.api import DEFAULT_CURRENCY
from modules.household.dtos import HouseholdStateDTO, HouseholdSnapshotDTO
from modules.household.services import HouseholdSnapshotAssembler
from modules.market.loan_api import (
    calculate_monthly_income,
    calculate_total_monthly_debt_payments
)

if TYPE_CHECKING:
    from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
    from modules.simulation.dtos.api import HouseholdConfigDTO

logger = logging.getLogger(__name__)

class HouseholdStateAccessMixin:
    """
    Mixin for accessing Household state.
    Provides methods to create DTOs and snapshots.
    """

    # Type hints for properties expected on self
    id: int
    config: "HouseholdConfigDTO"
    _bio_state: "BioStateDTO"
    _econ_state: "EconStateDTO"
    _social_state: "SocialStateDTO"
    preference_asset: float
    preference_social: float
    preference_growth: float
    risk_aversion: float

    def get_bio_state(self) -> "BioStateDTO":
        """Returns the biological state DTO."""
        return self._bio_state

    def get_econ_state(self) -> "EconStateDTO":
        """Returns the economic state DTO."""
        return self._econ_state

    def get_social_state(self) -> "SocialStateDTO":
        """Returns the social state DTO."""
        return self._social_state

    def _calculate_monthly_debt_payments(self) -> float:
        """
        Internal helper to calculate precise monthly debt payments by querying the bank.
        Used by both snapshot and legacy DTO creation to ensure parity.
        """
        decision_engine = getattr(self, 'decision_engine', None)
        loan_market = getattr(decision_engine, 'loan_market', None) if decision_engine else None
        ticks_per_year = getattr(self.config, 'ticks_per_year', 360)

        bank_service = None
        if loan_market and hasattr(loan_market, 'bank'):
            bank_service = loan_market.bank

        return calculate_total_monthly_debt_payments(bank_service, self.id, ticks_per_year)

    def create_snapshot_dto(self) -> HouseholdSnapshotDTO:
        """
        Creates a structured snapshot of the household's current state.
        Uses HouseholdSnapshotAssembler to ensure deep copies of component states.
        """
        # Calculate derived financial metrics for snapshot
        ticks_per_year = getattr(self.config, 'ticks_per_year', 360)
        monthly_income = calculate_monthly_income(self._econ_state.current_wage, ticks_per_year)

        monthly_debt_payments = self._calculate_monthly_debt_payments()

        # We need to pass 'self' to assemble, but 'self' here is the mixin instance,
        # which will be the Household instance at runtime.
        return HouseholdSnapshotAssembler.assemble(
            self,
            monthly_income=monthly_income,
            monthly_debt_payments=monthly_debt_payments
        )

    def create_state_dto(self) -> HouseholdStateDTO:
        """
        [DEPRECATED] Use create_snapshot_dto instead.
        Creates a comprehensive DTO of the household's current state (Adapter).
        """
        ticks_per_year = getattr(self.config, 'ticks_per_year', 360)
        monthly_income = calculate_monthly_income(self._econ_state.current_wage, ticks_per_year)
        monthly_debt_payments = self._calculate_monthly_debt_payments()

        # Convert DurableAssetDTOs to dicts for legacy compatibility
        durable_assets_legacy = []
        for d in self._econ_state.durable_assets:
            durable_assets_legacy.append({
                'item_id': d.item_id,
                'quality': d.quality,
                'remaining_life': d.remaining_life
            })

        return HouseholdStateDTO(
            id=self.id,
            assets=self._econ_state.assets,
            inventory=self._econ_state.inventory.copy(),
            needs=self._bio_state.needs.copy(),
            preference_asset=self.preference_asset,
            preference_social=self.preference_social,
            preference_growth=self.preference_growth,
            personality=self._social_state.personality,
            durable_assets=durable_assets_legacy,
            expected_inflation=self._econ_state.expected_inflation.copy(),
            is_employed=self._econ_state.is_employed,
            current_wage=self._econ_state.current_wage,
            wage_modifier=self._econ_state.wage_modifier,
            is_homeless=self._econ_state.is_homeless,
            residing_property_id=self._econ_state.residing_property_id,
            owned_properties=list(self._econ_state.owned_properties),
            portfolio_holdings={k: copy.copy(v) for k, v in self._econ_state.portfolio.holdings.items()},
            risk_aversion=self.risk_aversion,
            agent_data=self.get_agent_data(),
            conformity=self._social_state.conformity,
            social_rank=self._social_state.social_rank,
            approval_rating=self._social_state.approval_rating,
            optimism=self._social_state.optimism,
            ambition=self._social_state.ambition,
            perceived_fair_price=self._econ_state.perceived_avg_prices.copy(),
            sentiment_index=self._social_state.optimism,
            perceived_prices=self._econ_state.perceived_avg_prices.copy(),
            demand_elasticity=getattr(self._social_state, 'demand_elasticity', 1.0),
            monthly_income=monthly_income,
            monthly_debt_payments=monthly_debt_payments
        )

    def get_agent_data(self) -> Dict[str, Any]:
        """Adapter for AI learning data."""
        return {
            "assets": self._econ_state.assets.get(DEFAULT_CURRENCY, 0.0),
            "assets_dict": self._econ_state.assets.copy(), # Keep full dict available just in case
            "needs": self._bio_state.needs.copy(),
            "is_active": self._bio_state.is_active,
            "is_employed": self._econ_state.is_employed,
            "current_wage": self._econ_state.current_wage,
            "employer_id": self._econ_state.employer_id,
            "social_status": self._social_state.social_status,
            "credit_frozen_until_tick": self._econ_state.credit_frozen_until_tick,
            "is_homeless": self._econ_state.is_homeless,
            "owned_properties_count": len(self._econ_state.owned_properties),
            "residing_property_id": self._econ_state.residing_property_id,
            "social_rank": self._social_state.social_rank,
            "conformity": self._social_state.conformity,
            "approval_rating": self._social_state.approval_rating,
            "age": self._bio_state.age,
            "education_level": self._econ_state.education_level,
            "children_count": len(self._bio_state.children_ids),
            "expected_wage": self._econ_state.expected_wage,
            "gender": self._bio_state.gender,
            "home_quality_score": self._econ_state.home_quality_score,
            "spouse_id": self._bio_state.spouse_id,
            "aptitude": self._econ_state.aptitude,
        }
