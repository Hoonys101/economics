from __future__ import annotations
from typing import Optional, List, Any
import logging

from modules.market.housing_planner_api import (
    IHousingPlanner, HousingOfferRequestDTO, HousingDecisionDTO, LoanApplicationDTO
)
from modules.system.api import HousingMarketUnitDTO, HousingMarketSnapshotDTO
from modules.household.dtos import HouseholdStateDTO

logger = logging.getLogger(__name__)

class HousingPlanner(IHousingPlanner):
    """
    Stateless component that contains all business logic for housing decisions.
    Centralizes logic for Buying, Renting, and Staying.
    """

    # Constants (Fallback if config not provided)
    DEFAULT_DOWN_PAYMENT_PCT = 0.20

    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        household: HouseholdStateDTO = request['household_state']
        market: HousingMarketSnapshotDTO = request['housing_market_snapshot']

        # 1. Assess Urgency
        urgency = "LOW"
        if household.is_homeless:
            urgency = "HIGH"

        # 2. Evaluate "Buy" Option
        # Use simple affordability metric: Price <= Assets / DownPaymentPct
        max_price = household.assets / self.DEFAULT_DOWN_PAYMENT_PCT

        affordable_properties = []
        if market.for_sale_units:
            for prop in market.for_sale_units:
                if prop.price <= max_price:
                    # Simple Score: Quality / Price (Value for Money)
                    score = prop.quality / prop.price if prop.price > 0 else 0
                    affordable_properties.append((score, prop))

        # Sort by score desc
        affordable_properties.sort(key=lambda x: x[0], reverse=True)
        best_buy_option = affordable_properties[0][1] if affordable_properties else None

        # 3. Evaluate "Rent" Option
        # (Rental logic placeholder as units_for_rent is typically empty currently)
        best_rent_option = None
        if market.units_for_rent:
             # Basic logic: Rent <= 30% of Income (Approximation)
             # As we lack income data in Request DTO, we might skip or use naive check
             # For now, just pick cheapest
             sorted_rentals = sorted(market.units_for_rent, key=lambda x: x.rent_price if x.rent_price else float('inf'))
             if sorted_rentals:
                 best_rent_option = sorted_rentals[0]

        # 4. Compare and Decide

        # Case A: Homeless - Must act
        if household.is_homeless:
            if best_buy_option:
                return self._create_buy_decision(best_buy_option, household)
            elif best_rent_option:
                return HousingDecisionDTO(
                    decision_type="RENT",
                    target_property_id=best_rent_option.unit_id,
                    offer_price=best_rent_option.rent_price,
                    loan_application=None
                )
            else:
                # No options available
                return HousingDecisionDTO(
                    decision_type="DO_NOTHING",
                    target_property_id=None,
                    offer_price=None,
                    loan_application=None
                )

        # Case B: Upgrade / Voluntary Move
        # Logic: IF Buy Option exists AND (Better than Rent OR Mode is BUY)
        should_buy = False
        if best_buy_option:
            # Calculate Scores (Quality / Price)
            buy_score = best_buy_option.quality / best_buy_option.price if best_buy_option.price > 0 else 0

            rent_score = -1.0
            if best_rent_option:
                 rent_score = best_rent_option.quality / best_rent_option.rent_price if best_rent_option.rent_price > 0 else 0

            # 1. Explicit Desire (System 2 legacy / External override)
            if hasattr(household, 'housing_target_mode') and household.housing_target_mode == "BUY":
                should_buy = True

            # 2. Rational Choice (Spec Logic)
            # If buying is better than renting (or renting is impossible), and we can afford it.
            # Note: We already filtered best_buy_option for affordability.
            elif buy_score > rent_score:
                 should_buy = True

        if should_buy and best_buy_option:
            return self._create_buy_decision(best_buy_option, household)

        # Default: Stay
        return HousingDecisionDTO(
            decision_type="STAY",
            target_property_id=None,
            offer_price=None,
            loan_application=None
        )

    def _create_buy_decision(self, prop: HousingMarketUnitDTO, household: HouseholdStateDTO) -> HousingDecisionDTO:
        offer_price = prop.price
        required_down = offer_price * self.DEFAULT_DOWN_PAYMENT_PCT

        # Ensure we don't apply for negative loan (if assets cover full price)
        # But usually we take mortgage to leverage.
        # Logic: Pay minimum down payment.

        loan_amount = offer_price - required_down

        loan_app = LoanApplicationDTO(
            applicant_id=household.id,
            principal=loan_amount,
            purpose="MORTGAGE",
            property_id=prop.unit_id,
            offer_price=offer_price
        )

        return HousingDecisionDTO(
            decision_type="MAKE_OFFER",
            target_property_id=prop.unit_id,
            offer_price=offer_price,
            loan_application=loan_app
        )
